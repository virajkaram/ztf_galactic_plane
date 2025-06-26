from emgwcave.kowalski_utils import  get_find_query
from emgwcave.candidate_utils import make_photometry
import numpy as np


def search_galactic_plane_candidates(k, jd_start: float, jd_end: float,
                                     catalog: str='ZTF_alerts',
                                     filter_kwargs: dict = {},
                                     max_n_threads: int = 8):
    """Search for candidates in the galactic plane using Kowalski."""
    magamp = 4.0
    query = get_find_query(
        catalog=catalog,
        filter={
            "candidate.jd": {"$gt": jd_start, "$lt": jd_end},
            "candidate.drb": {"$gt": 0.5},
            "candidate.ndethist": {"$gt": 5},
            "candidate.isdiffpos": {'$in': ['t', '1', True, 1]},
            "coordinates.b": {"$gt": -10, "$lt": 10},
            "$or": [
                {"candidate.distpsnr1": {"$gt": 2.0}},
                {"$and":
                    [{"candidate.distpsnr1": {"$lt": 2.0}},
                     {"$expr": {"$gt": [
                        {"$subtract": ["$candidate.srmag1", "$candidate.magpsf"]},
                        magamp]}}]},
                {"$and": [{"candidate.distpsnr1": {"$lt": 2.0}},
                            {"candidate.srmag1": {"$eq": -999.0}},
                          {"$or": [{"candidate.distpsnr2": {"$lt": 2.0}},
                                   {"$expr":
                                       {"$gt": [{"$subtract": [
                                          "$candidate.srmag2", "$candidate.magpsf"]},
                                                        magamp]}}]}]}
                    ],
        },
        projection={'_id': 0,
                    'cutoutScience': 0,
                    'cutoutTemplate': 0,
                    'cutoutDifference': 0,
                    },
        query_kwargs=filter_kwargs,
    )

    candidates = k.query(query=query, use_batch_query=True, max_n_threads=max_n_threads)
    return candidates['default']['data']



def filter_galactic_plane_candidates(candidates: list[dict]):
    """Filter candidates in the galactic plane based on specific criteria."""
    filtered_candidates = []
    for candidate in candidates:
        candidate['candidate']['deltajd'] = candidate['candidate']['jdendhist'] - candidate['candidate']['jdstarthist']
        if (((20 < candidate['candidate']['deltajd']) and (candidate['candidate']['deltajd'] < 200))
                and
                ((candidate['candidate']['ssdistnr']>2) or (candidate['candidate']['ssdistnr']<-0.5))) :
            filtered_candidates.append(candidate)
    return filtered_candidates


def filter_candidate_duration(candidates: list[dict]):
    filtered_candidates = []
    for candidate in candidates:
        photometry_df = make_photometry(candidate)
        detected = np.isfinite(photometry_df["magpsf"])
        age = photometry_df[detected]['mjd'].max() - photometry_df[detected]['mjd'].min()
        if 20 < age < 200:
            filtered_candidates.append(candidate)

    return filtered_candidates
