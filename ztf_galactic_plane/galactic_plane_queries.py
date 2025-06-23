from emgwcave.kowalski_utils import connect_kowalski, get_find_query, query_aux_alerts


def search_hostless_galactic_plane_candidates(k, jd_start: float, jd_end: float,
                                              catalog: str='ZTF_alerts',
                                              filter_kwargs: dict = {},
                                              max_n_threads: int = 8):
    """Search for candidates in the galactic plane using Kowalski."""
    query = get_find_query(
        catalog=catalog,
        filter={'candidate.jd': {'$gte': jd_start, '$lte': jd_end},
                "coordinates.b": {"$gt": -10, "$lt": 10},
                "candidate.drb": {"$gt": 0.95},
                "candidate.isdiffpos": 't',
                "candidate.distpsnr1": {"$gt": 2.0},
                "candidate.ndethist": {"$gt": 20},
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
        if (20 < candidate['candidate']['deltajd']) and (candidate['candidate']['deltajd'] < 200) :
            filtered_candidates.append(candidate)
    return filtered_candidates
