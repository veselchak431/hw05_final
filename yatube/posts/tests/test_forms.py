from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, Comment

User = get_user_model()


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.image = SimpleUploadedFile(
            name='small.png',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.wrong_image = SimpleUploadedFile(
            name='small.pppppp',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.image
        }

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        # Проверяем, увеличилось ли число постов

        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group
            ).exists())

    def test_wrong_file_upload(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.wrong_image
        }

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group
            ).exists())

    def test_edit_post(self):
        """Валидная форма создает запись в Post."""
        posts_data = Post.objects.filter(id=self.post.id)
        form_data = {
            'text': 'измененный текст',
            'group': self.group.id
        }

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))

        self.assertNotEqual(posts_data, Post.objects.filter(id=self.post.id))

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.filter(post=self.post).count()
        form_data = {
            'text': 'Тестовый текст комментария'}

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        # Проверяем, увеличилось ли число постов

        self.assertEqual(Comment.objects.filter(
            post=self.post).count(), comments_count + 1)
        # Проверяем, что создался комментарий
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый текст комментария'
            ).exists())
