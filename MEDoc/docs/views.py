from django.views.generic import ListView
from .models import Doc, Subject, DocFolderType
from django.db.models import Q


class DocSearch(ListView):
    model = Doc
    paginate_by = 50
    template_name = 'docs/doc_search.html'
    ordering = ('subject', 'doc_type')

    def get_queryset(self):
        q_words = self.request.GET.get("q")
        q_words = q_words.split(' ')
        queryset = Doc.objects.filter(is_folder=False)

        subjects = list(Subject.objects.filter(Q(short_title__icontains=q_words[0]) | Q(title__icontains=q_words[0])))
        if subjects:
            queryset = queryset.filter(subject__in=subjects)
            q_words.pop(0)
            if q_words:
                doc_types = list(DocFolderType.objects.filter(Q(title__icontains=q_words[1]) |
                                                              Q(title_plural__icontains=q_words[0])))
                if doc_types:
                    queryset = queryset.filter(type__in=doc_types)
                    q_words.pop(0)
        for word in q_words:
            queryset = queryset.filter(title__icontains=word)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['q'] = self.request.GET.get('q')
        context['title'] = 'Поиск'
        return context


class DocListView(ListView):
    template_name = 'docs/doc_list_view.html'
    queryset = Doc.objects.all()

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **{'title': 'Документы'}}