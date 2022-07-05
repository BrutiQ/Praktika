from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст товара',
            'group': 'Подборка товара',
            'image': 'Картинка товара',
        }
        help_texts = {
            'text': 'Введите описание товара',
            'group': 'Выберите категорию товаров',
            'image': 'Выберите картинку для нового товара',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария.'
        }
        help_texts = {
            'text': 'Напишите комментарий.'
        }
