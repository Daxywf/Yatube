from django.core.paginator import Paginator


def posts_page(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
