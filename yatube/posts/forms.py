from django import forms

from .models import Follow, Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {'text': 'Текст поста',
                  'group': 'Группа',
                  'image': 'Картинка',
                  }
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        labels = {'text': 'Текст комментария',
                  'created': 'Дата создания'
                  }
        fields = ['text']


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        labels = {'user': 'Подписка на:', 'author': 'Автор записи'}
        fields = ['user']
