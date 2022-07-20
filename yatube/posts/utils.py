from django.core.paginator import Paginator


def paginator_project(request, name):
    NUM_REC: int = 10
    paginator = Paginator(name, NUM_REC)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
