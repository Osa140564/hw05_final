from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

import shutil
import tempfile

from posts.models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name1')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовая запись',
            id='1',
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': cls.post.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'test_name1'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': cls.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Solid')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_about_page_uses_correct_template(self):

        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image
        self.assertEqual(post_text_0,
                         'Тестовая запись')
        self.assertEqual(post_author_0, 'test_name1')
        self.assertEqual(post_group_0, 'Заголовок')
        self.assertEqual(post_image_0, self.post.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.post.group.slug}))
        first_object = response.context["group"]
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'Заголовок')
        self.assertEqual(group_slug_0, 'test_slug1')

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}))
        first_object = response.context['page_obj'][0]
        post_title_0 = first_object.author.username
        post_text_0 = first_object.text
        post_slug_0 = first_object.group.slug
        self.assertEqual(post_title_0, 'test_name1')
        self.assertEqual(post_text_0, 'Тестовая запись')
        self.assertEqual(post_slug_0, 'test_slug1')

    def test_new_post_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.post.author.username}))
        first_object = response.context['page_obj'][0]
        post_title_0 = first_object.author.username
        post_text_0 = first_object.text
        post_slug_0 = first_object.group.slug
        post_image_0 = first_object.image
        self.assertEqual(post_title_0, 'test_name1')
        self.assertEqual(post_text_0, 'Тестовая запись')
        self.assertEqual(post_slug_0, 'test_slug1')
        self.assertEqual(post_image_0, self.post.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(
                Post(text='Тест пост ' + str(i),
                     author=cls.author,
                     group=cls.group)
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='ss')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse("posts:index"): "index",
            reverse("posts:group_list", kwargs={
                "slug": "test_slug2"}): "group",
            reverse("posts:profile", kwargs={
                "username": "test_name"}): "profile",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse("posts:index") + "?page=2": "index",
            reverse("posts:group_list", kwargs={
                "slug": "test_slug2"}) + "?page=2":
            "group",
            reverse("posts:profile", kwargs={
                "username": "test_name"}) + "?page=2":
                    "profile",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list), 3)

    def test_add_comments(self):
        post = Post.objects.last()
        form_data = {
            'text': 'test comment'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ), data=form_data
        )
        self.assertEqual(response.status_code, 302)
        response1 = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(len(response1.context['comments']), 1)

    def test_index_page_caches_content(self):
        """Страница index отдает кэшированный контент."""
        response = self.client.get(reverse('posts:index'))
        content_old = response.content
        Post.objects.create(
            text='test cache index page',
            author=self.user,
            group=self.group
        )
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, content_old)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, content_old)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name1')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug1',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовая запись',
            id='1',
        )
        cls.user_is_following_author = User.objects.create_user(
            username='UserIsFollowingAuthor'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Solid')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_usr_is_fol_author = Client()
        self.authorized_usr_is_fol_author.force_login(
            self.user_is_following_author
        )
        self.auth_usr_is_not_fol_author = Client()
        self.auth_usr_is_not_fol_author.force_login(
            self.user_is_following_author
        )

    def test_new_post_for_follower(self):
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.author
        )
        Follow.objects.create(
            user=self.user_is_following_author,
            author=self.author
        )
        response = self.authorized_usr_is_fol_author.get(
            reverse('posts:follow_index')
        )
        new_posts = response.context.get(
            'page_obj'
        ).object_list
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост не виден follower'
        )

    def test_new_post_unavailable_for_unfollower(self):
        new_post = Post.objects.create(
            text='test_new_post_for_unfollower',
            group=self.group,
            author=self.author
        )
        response = self.auth_usr_is_not_fol_author.get(
            reverse('posts:follow_index')
        )
        new_posts = response.context.get(
            'page_obj'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост виден unfollower.'
        )
