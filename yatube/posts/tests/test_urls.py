from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        self.second_user = User.objects.create_user(username='SecondUser')
        self.authorized_second_client = Client()
        self.authorized_second_client.force_login(self.second_user)

    def test_urls_uses_correct_template_authorized_client(self):
        templates_url_names = {
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest_client_try_update_post(self):
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        redirect_url = f'/posts/{self.post.id}/'
        response = self.guest_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_urls_guest_client_try_make_comment(self):
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        redirect_url = f'/posts/{self.post.id}/'
        response = self.guest_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_urls_not_author_try_update_post(self):
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        redirect_url = f'/auth/login/?next=/posts/{self.post.id}/comment/'
        response = self.guest_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_urls_unexisting_page(self):
        response = self.guest_client.get('/abra-cadabra/')
        self.assertEqual(response.status_code, 404)

    def test_404_error_use_correct_template(self):
        """404 ошибка использует соответствующий шаблон."""
        response = self.guest_client.get('/abra-cadabra/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)

    def test_urls_guest_client_try_follow(self):
        url = reverse('posts:profile_follow',
                      kwargs={'username': self.second_user})
        redirect_url = f'/auth/login/?next=/profile/{self.second_user}/follow/'

        response = self.guest_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_urls_authorized_client_try_follow(self):
        url = reverse('posts:profile_follow',
                      kwargs={'username': self.second_user})
        redirect_url = f'/profile/{self.second_user}/'
        response = self.authorized_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_urls_authorized_client_try_unfollow(self):
        url = reverse('posts:profile_unfollow',
                      kwargs={'username': self.second_user})
        redirect_url = f'/profile/{self.second_user}/'
        response = self.authorized_client.get(url)
        self.assertRedirects(response, redirect_url)
