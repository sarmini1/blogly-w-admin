import os

os.environ["DATABASE_URL"] = "postgresql:///blogly_test"

from unittest import TestCase

from app import app, db
from models import DEFAULT_IMAGE_URL, User, Post

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        Post.query.delete()
        User.query.delete()

        self.client = app.test_client()

        test_user = User(
            first_name="test1_first",
            last_name="test1_last",
            image_url=None,
        )

        test_user2 = User(
            first_name="test2_first",
            last_name="test2_last",
            image_url=None,
        )

        db.session.add_all([test_user, test_user2])
        db.session.commit()

        self.user_id = test_user.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_list_users(self):
        with self.client as c:
            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_first", html)
            self.assertIn("test1_last", html)

    def test_add_new_user(self):
        with self.client as c:
            resp = c.post(
                "/users/new",
                data={
                    "first_name": "newuser_first",
                    "last_name": "newuser_last",
                    "image_url": "https://new.com",
                },
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("newuser", html)

    def test_add_new_user_no_image(self):
        with self.client as c:
            resp = c.post(
                "/users/new",
                data={
                    "first_name": "no_image_first",
                    "last_name": "no_image_last",
                    "image_url": "",
                },
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

    def test_show_user(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user_id}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_first", html)
            self.assertIn("test1_last", html)
            self.assertIn(DEFAULT_IMAGE_URL, html)

    def test_show_edit_form(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user_id}/edit")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_first", html)
            self.assertIn("test1_last", html)
            self.assertIn(DEFAULT_IMAGE_URL, html)

    def test_update_user(self):
        with self.client as c:
            resp = c.post(
                f"/users/{self.user_id}/edit",
                data={
                    "first_name": "updated_first",
                    "last_name": "updated_last",
                    "image_url": "https://test.com/",
                },
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("updated_first", html)
            self.assertIn("updated_last", html)

    def test_delete_user(self):
        with self.client as c:
            # add a post for this user and make sure it deletes the post as well

            test_post = Post(
                title="test_message_delete",
                content="test_content_delete",
                user_id=self.user_id,
            )

            db.session.add(test_post)
            db.session.commit()

            resp = c.post(
                f"/users/{self.user_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("User test1_first test1_last deleted.", html)

            self.assertNotIn(f"/users/{self.user_id}", html)

            resp = c.get(f"/posts/{test_post.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 404)

            self.assertEqual(User.query.count(), 1)


class PostViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        Post.query.delete()
        User.query.delete()

        self.client = app.test_client()

        test_user = User(
            first_name="test1_first",
            last_name="test1_last",
            image_url=None,
        )

        db.session.add(test_user)
        db.session.commit()

        # we need the test user id to exist before creating a post
        test_post = Post(
            title="test1_title",
            content="test1_content",
            user_id=test_user.id,
        )

        db.session.add(test_post)
        db.session.commit()

        self.user_id = test_user.id
        self.post_id = test_post.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_list_posts_for_user(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user_id}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_title", html)

    def test_add_new_post(self):
        with self.client as c:
            resp = c.post(
                f"/users/{self.user_id}/posts/new",
                data={
                    "title": "new_title",
                    "content": "new_content",
                },
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("new_title", html)

    def test_show_post(self):
        with self.client as c:
            resp = c.get(f"/posts/{self.post_id}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_title", html)
            self.assertIn("test1_content", html)

    def test_show_post_edit(self):
        with self.client as c:
            resp = c.get(f"/posts/{self.post_id}/edit")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("test1_title", html)
            self.assertIn("test1_content", html)

    def test_update_post(self):
        with self.client as c:
            resp = c.post(
                f"/posts/{self.post_id}/edit",
                data={
                    "title": "updated_title",
                    "content": "updated_content",
                },
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("Post updated_title edited.", html)

    def test_delete_post(self):
        with self.client as c:
            resp = c.post(
                f"/posts/{self.post_id}/delete",
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn(f"Post test1_title deleted.", html)

            self.assertNotIn(f"/posts/{self.post_id}", html)
