from typing import Any, List
import math

def get_pages_nav(total_pages, current_page):
    next_page = None
    prev_page = None
    if current_page + 1 <= total_pages:
        next_page = current_page + 1
    if current_page - 1 >= 1:
        prev_page = current_page - 1
    return next_page, prev_page


def paginate_data(
        data: List[dict],
        page_no:int,
        page_size:int,
        total_content:int
    ):
    total_pages = math.ceil(total_content / page_size)
    next_page, prev_page = get_pages_nav(total_pages, page_no)

    return {
        'count':total_content,
        'next_page':next_page,
        'prev_page':prev_page,
        'results':data
    }
