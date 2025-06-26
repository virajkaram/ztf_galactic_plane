import argparse
from astropy.time import Time
from emgwcave.kowalski_utils import connect_kowalski
from emgwcave.plotting import save_thumbnails, make_full_pdf
from emgwcave.candidate_utils import save_candidates_to_file, \
    append_photometry_to_candidates, write_photometry_to_file, get_thumbnails, \
    deduplicate_candidates, \
    get_candidates_crossmatch, annotate_candidates
from time import sleep
import os

from pathlib import Path
from ztf_galactic_plane.galactic_plane_queries import \
    (filter_galactic_plane_candidates,
     search_galactic_plane_candidates, filter_candidate_duration)
import numpy as np


def setup_output_directories(output_dir: str):
    phot_dir = os.path.join(output_dir, 'photometry')
    thumbnails_dir = os.path.join(output_dir, 'thumbnails')
    for d in [phot_dir, thumbnails_dir]:
        if not os.path.exists(d):
            Path(d).mkdir(parents=True, exist_ok=True)

    return phot_dir, thumbnails_dir


def plot_galactic_candidates(all_candidates, plotfile, kowalski):
    all_candidates = deduplicate_candidates(all_candidates)

    all_candidates = get_candidates_crossmatch(all_candidates, k=kowalski)
    all_candidates = annotate_candidates(all_candidates)
    all_candidates = get_thumbnails(all_candidates, k=kowalski)
    save_thumbnails(all_candidates,
                    thumbnails_dir=thumbnails_dir,
                    plot=args.plot_thumbnails_separately)

    write_photometry_to_file(all_candidates,
                             phot_dir=phot_dir,
                             plot=args.plot_lightcurves_separately)
    make_full_pdf(all_candidates,
                  thumbnails_dir=thumbnails_dir,
                  phot_dir=phot_dir,
                  pdffilename=plotfile,
                  )


def find_galactic_candidates(kowalski,
                             start_date_jd: float,
                             end_date_jd: float,
                             instrument: str = 'ZTF',
                             outdir='galactic_plane_output',
                             nthreads: int = 8,
                             ):
    # Set up Kowalski connection and run query
    # Split queries into 0.5 day chunks to avoid timeouts
    all_candidates = np.array([])
    iter_counter = 0
    savefile = os.path.join(outdir, f"galactic_plane_candidates_{instrument}"
                                    f"_alerts_{round(start_date_jd, 2)}_"
                                    f"{round(end_date_jd, 2)}.csv")

    jd_start = start_date_jd
    jd_interval = 0.2  # 0.2 days chunk size
    resume_iter = np.inf
    while jd_start < end_date_jd:
        if iter_counter > resume_iter:
            jd_interval = 0.2
            resume_iter = np.inf
        jd_end = jd_start + jd_interval
        print(f"Searching for candidates between {jd_start} and {jd_end}")
        try:
            candidates = search_galactic_plane_candidates(k=kowalski,
                                                              jd_start=jd_start,
                                                              jd_end=jd_start + jd_interval,
                                                              catalog=f'{instrument}_alerts',
                                                              max_n_threads=nthreads,
                                                              )
        except Exception as e:
            # Try with a smaller chunk size ten times smaller, for the next ten iterations.
            if jd_interval <= 0.01:
                print(f"{e}: {jd_start} to {jd_end}. "
                      f"Giving up after trying 10 times with smaller chunk size {jd_interval}.")
                break
            print(f"{e}: Trying with smaller chunk size.")
            jd_interval /= 10
            resume_iter = iter_counter + 10
            continue

        jd_start += jd_interval  # Move to the next chunk
        if len(candidates) == 0:
            continue

        iter_counter += 1
        candidates = filter_galactic_plane_candidates(candidates)
        print(f"Found {len(candidates)} candidates "
              f"between {jd_start - jd_interval} and {jd_end}")
        # Get full photometry history for the selected candidates
        candidates = append_photometry_to_candidates(candidates, k=kowalski)
        candidates = filter_candidate_duration(candidates)

        all_candidates = np.append(all_candidates, candidates)

        # Write candidates to file every 10 candidates, or in the last chunk
        if (iter_counter % 10 == 0) | (jd_start + jd_interval >= end_date_jd):
            save_candidates_to_file(all_candidates, savefile=savefile)

        sleep(1)  # Sleep to avoid hitting rate limits

    return all_candidates


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir", type=str,
                        help='name of output directory for plots etc.')
    parser.add_argument('start_date', type=str,
                        help="Search for candidates that were first "
                             "detected after this day e.g. 2023-04-23T00:00:00")
    parser.add_argument("end_date", type=str,
                        help='Search for candidates first detected '
                             'before this day, e.g. 2023-04-23T00:00:00 ',
                        default=None
                        )
    parser.add_argument("-instrument", type=str, choices=["ZTF", "WNTR"], default='ZTF')
    parser.add_argument("-filter", type=str, choices=['none', 'fritz'],
                        help='What filter do you want to use?', default='fritz'
                        )
    parser.add_argument("-nthreads", type=int, help="How many threads "
                                                    "to use on kowalski",
                        default=8)
    parser.add_argument("-plot_lightcurves_separately", action="store_true")
    parser.add_argument("-plot_thumbnails_separately", action="store_true")
    parser.add_argument("-groupids", type=str, default='48',
                        help="Group ID on fritz, e.g. 48,49")

    args = parser.parse_args()

    start_date_jd = Time(args.start_date).jd

    end_date_jd = Time(args.end_date).jd

    # Set up paths and directories
    output_dir = args.outdir

    savefile = os.path.join(output_dir,
                            f"galactic_plane_candidates"
                            f"_{args.instrument}_alerts"
                            f"_{args.start_date}_{args.end_date}"
                            f".csv")

    phot_dir, thumbnails_dir = setup_output_directories(output_dir)

    kowalski = connect_kowalski()

    selected_candidates = find_galactic_candidates(kowalski=kowalski,
                                                   instrument=args.instrument,
                                                   start_date_jd=start_date_jd,
                                                   end_date_jd=end_date_jd,
                                                   nthreads=args.nthreads,
                                                   outdir=output_dir)

    print(f"Found {len(selected_candidates)} candidates in total.")
    plotfile = savefile.replace('.csv', '.pdf')
    plot_galactic_candidates(selected_candidates, plotfile, kowalski=kowalski)
