from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_author_url_exists_at_desired_location(self):
        """Проверка доступности адреса /page/about/."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response, 'about/author.html')

    def test_about_tech_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/tech/."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/tech/."""
        response = self.guest_client.get('/about/tech/')
        self.assertTemplateUsed(response, 'about/tech.html')


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            id='1',
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_slug_url_exists_at_desired_location(self):
        """Страница /group/test_slug/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test_slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_username_url_exists_at_desired_location(self):
        """Страница /profile/<username>/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/HasNoName/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_url_exists_at_desired_location(self):
        """Страница /group/<slug> доступна любому пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ не доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_posts_post_id_edit_url__exists_at_desired_location(self):
        """Страница /posts/post_id/edit/ переадресует
         любого пользователя."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_not_exists_at_desired_location(self):
        """Страница /create/ не  доступна любому пользователю."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_task_list_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_post_detail(self):
        response = self.client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/')

    def test_add_comments_urls_anonymous(self):
        response = self.guest_client.get('/posts/1/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
