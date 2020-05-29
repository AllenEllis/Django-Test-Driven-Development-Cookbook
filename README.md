
# The Django Test Driven Development Cookbook
This is an annotation of the slides from [this YouTube talk](https://www.youtube.com/watch?v=41ek3VNx_6Q).

> Speaker: Martin Brochhaus
>
> Martin is currently working as the CTO of theartling.com and luxglove.com and is maintaining a codebase with ~30k lines of code and ~12k lines of tests. In this 45 minutes talk, he will show how you can setup your first Django test-suite with py.test, how you can create fixtures with mixer and how you can measure test coverage. He will also show common patterns and snippets that will help you overtake the initial hurdles of getting in to testing: How to speed up tests? How to mock third party libraries? How to test forms and class based views with Django's RequestFactory? How to test admin functions and management commands? How to test Django Rest Framework's API views and serializers?
>
> Event Page: http://www.meetup.com/Singapore-Djang...
>
> Produced by Engineers.SG

### Slide 4
Agenda:
 - Project Setup
 - Testing Models
 - Testing Admins
 - Testing Views
 - Testing Authentication
 - Testing Forms
 - Testing POST Requests
 - Testing 404 Errors
 - Mocking Requests

### Slide 5
Project Setup

Let's create a new Django project

```bash
mkvirtualenv tried_and_tested
pip install Django
django-admin.py startproject tested
```

### Slide 6
Add a `test_settings.py` file
```bash
cd tested/tested
touch test_settings.py
```

### Slide 7
Install pytest & plugins and create "pytest.ini"

```bash
pip install pytest
pip install ptest-django
pip install git+git://github.com/mverteuil/pytest-ipdb.git
pip install pytest-cov
deactivate
workon tried_and_tested
```

####`pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = tested2.test_settings
addopts = --nomigrations --cov=. --cov-report=html
```


### Slide 8
Put this code into `.coveragerc`
```ini
[run]
omit =
    *apps.py,
    *migrations/*,
    *settings*,
    *tests/*,
    *urls.py,
    *wsgi.py,
    manage.py
```

### Slide 9
- We are ready to test!
- `py.test` will find all files called `test_*.py`
- It wll execute all functions called `test_*()` on all classes that start with `Test*`

### Slide 10
#### Testing Models
- Install `mixer` and create your first app
- Remove `tests.py` and create `tests` folder instead
- Each Django app will have a `tests` folder
- For each code file, i.e. `forms.py` we will have a test. I.e., `test_forms.py`

```shell
pip install mixer
django-admin.py startapp birdie
rm birdie/tests.py
mkdir birdie/tests
touch birdie/tests/__init__.py
touch birdie/tests/test_models.py
```


### Slide 11
- The main building block of most apps is a model
- We should start writing a test for our model
- Some models can have many mandatory fields and it can be quite tedious to create values for all those fields. `mixer` will help here.

### Slide 12
Let's test if the model can be instantiated and saved:

```python
# test_models.py
from mixer.backend.django import mixer

pytestmark = pytest.mark.django_db


class TestPost:
    def test_init(self):
        obj = mixer.blend('birdie.Post')
        assert obj.pk == 1, 'Should save an instance'
```

### Slide 13
- Try to run your first test
- This tells you that you have not created a model named `Post` yet
- Also: Make sure to add `birdie` to your `INSTALLED_APPS` setting

### Slide 14
Implement the model and run your tests again

```python
from django.db import models

# Create your models here.

class Post(models.Model):
    body = models.TextField()
```

Your test should now pass and you have 100% coverage

### Slide 15
Testing models

- Imagine a model function that returns truncated body
- Before you implement the function, you have to write the test
- That means you have to "use" your function before it even exists
- This helps to think deeply about it, come up with a name, with allowed
  arguments, with type of return value, with different kids of invocations, etc

### Slide 16
The function shall be called `get_excerpt` and expect one argument

```python
# test_models.py
    def test_get_excerpt(self):
        obj = mixer.blend('birdie.Post', body="Hello World!")
        result = obj.get_excerpt(5)
        assert result == "Hello", "Should return first few characters"
```

Run your tests often and fix each error until they pass.

### Slide 17
Implement the function and run the tests again
```python
# models.py
class Post(models.Model):
    body = models.TextField()

    def get_excerpt(self, char):
        return self.body[:char]
```

Your test should now pass and you have 100% coverage

### Slide 18
Testing admins

 - We want to show the excerpt in our admin list view
 - We need to write a function for this because "excerpt" is not a database field on the model
 - Whenever we need to write a function, we know: We must also write  atest for that function
 - In order to instantiate an admin class, you must pass in a model class and an AdminSite() instance

### Slide 19
Instantiate your admin class and call the new `excerpt` function
```python
import pytest
from django.contrib.admin.sites import AdminSite
from mixer.backend.django import mixer
from .. import admin
from .. import models
pytestmark = pytest.mark.django_db

class TestPostAdmin:
    def test_excerpt(self):
        site = AdminSite()
        post_admin = admin.PostAdmin(models.Post, site)

        obj = mixer.blend('birdie.Post', body='Hello World')
        result = post_admin.excerpt(obj)
        assert result == 'Hello', "Should return first few characters"
```

### Slide 20
Implement the admin and run the tests again

```python
from django.contrib import admin
from . import models
# Register your models here.


class PostAdmin(admin.ModelAdmin):
    model = models.Post
    list_display = ('excerpt', )

    def excerpt(self, obj):
        return obj.get_excerpt(5)
```

### Slide 21
 - We want to create a view that can be seen by anyone
 - Django's `self.client.get()` is slow
 - We will use Django's `RequestFactory` instead
 - We can instantiate our class-based views just like we do it in our `urls.py`, via `ViewName.as_view()`
 - To test our views, we create a `Request`, pass it to our `View`, then make assertions on the returned `Response`
 - Treat class-based views as black-boxes

### Slide 22
We want to create a view that can be seen by anyone
```python
from django.test import RequestFactory
from .. import views


class TestHomeView:
    def test_anonymous(self):
        req = RequestFactory().get('/')
        resp = views.HomeView.as_view()(req)
        assert resp.status_code == 200, "Should be callable by anyone"
```

 ### Slide 23
 Implement the view and ru the tests again
 ```python
# views.py
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'birdie/home.html'
```
 - Your tests should pass with 100% coverage
 - This does NOT render the view and test the template
 - This does NOT call `urls.py`

 ### Slide 24
 Testing authentication:

  - We want to create a view that can only be accessed by superusers
  - We will use the `@method_decorator(login_required)` trick to protect our view
  - That means, that there must be a `.user` attribute on the Request.
  - Even if we want to rest as an anonymous user, in that case Django automatically
    attaches a `AnonymousUser` instance to the `Request`, so we have to fake this as well

### Slide 25
Testing authentication
```python
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db

from .. import views
import pytest

pytestmark = pytest.mark.django_db

...

class TestAdminView:
    def test_anonymous(self):
        req = RequestFactory().get('/')
        req.user = AnonymousUser()
        resp = views.AdminView.as_view()(req)
        assert 'login' in resp.url

    def test_superuser(self):
        user = mixer.blend('auth.User', is_superuser=True)
        req = RequestFactory().get('/')
        req.user = user
        resp = views.AdminView.as_view()(req)
        assert resp.status_code == 200, 'Authenticated user can access'

```

### Slide 26
Implement the view and run the tests again
```python
# test_views.py
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

...

class AdminView(TemplateView):
    template_name = 'birdie/admin.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AdminView, self).dispatch(request, *args, **kwargs)
```


### Slide 27
We want to create a form that creates a Post object
```python
# test_forms.py
import pytest
from .. import forms
pytestmark = pytest.mark.django_db


class TestPostForm:
    def test_form(self):
        form = forms.PostForm(data={})
        assert form.is_valid() is False, 'Should be invalid if not data given'

        form = forms.PostForm(data={'body': 'Hello'})
        assert form.is_valid() is False, 'Should be invalid if too short'
        assert 'body' in form.errors, 'Should have body field error'

        form = forms.PostForm(data={'body': 'Hello World!!!!!!!!!!!!'})
        assert form.is_valid() is True, "Should be valid if long enough"
```

### Slide 28
- When you implement the form step by step, you will see various test errors
- They guide you towards your final goal


### Slide 29
Implement the form and run the tests again
```python
# forms.py

from django import forms
from . import models


class PostForm(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ('body', )

    def clean_body(self):
        data = self.cleaned_data.get('body')
        if len(data) <= 5:
            raise forms.ValidationError("Message is too short")
        return data
```

### Slide 30
- We want to create a view that uses the PostForm to update a Post
- Testing POST requests works in the same way like GET requests
- The next example also shows how to pass POST data into the
  view and how to pass URL `kwargs` into the view


### Slide 31
Testing POST requests

```python
# test_views.py
import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db

from .. import views

...


class TestPostUpdateView:
    def test_get(self):
        req = RequestFactory().get('/')
        obj = mixer.blend('birdie.Post')
        resp = views.PostUpdateView.as_view()(req, pk=obj.pk)
        assert resp.status_code == 200, 'Should be callable by anyone'

    def test_post(self):
        post = mixer.blend('birdie.Post')
        data = {'body': 'New Body Text!'}
        req = RequestFactory().post('/', data=data)
        resp = views.PostUpdateView.as_view()(req, pk=post.pk)
        assert resp.status_code == 302, 'Should redirect to success view'
        post.refresh_from_db()
        assert post.body == 'New Body Text!', 'Should update the post'
```

### Slide 32
Implement the view

```python
# views.py
from django.views.generic import TemplateView, UpdateView

from . import models
from. import forms

class PostUpdateView(UpdateView):
    model = models.Post
    form_class = forms.PostForm
    template_name = '/birdie/update.html'
    success_url = '/'
```

### Slide 33
Testing 404 errors
- Your views will often raise 404 errors
- Unfortunately, they are exceptions and they bubble up all the way into your tests, so you cannot simply check
  `assert resp.status_code == 404`
- Instead, you have to execute the view inside a `with-statement`


### Slide 34
- If the user's name is "Martin", the PostUpdateView should raise a 404

```python
from django.http import Http404
...
class TestPostUpdateView:
    ...
    def test_security(self):
        user = mixer.blend('auth.User', first_name='Martin')
        post = mixer.blend('birdie.Post')
        req = RequestFactory().post('/', data={})
        req.user = user
        with pytest.raises(Http404):
            views.PostUpdateView.as_view()(req, pk=post.pk)
```

### Slide 35
Update your implementation
```python
# views.py
from django.http import Http404
...


class PostUpdateView(UpdateView):
    model = models.Post
    form_class = forms.PostForm
    template_name = '/birdie/update.html'
    success_url = '/'

    def post(self, request, *args, **kwargs):
        if getattr(request.user, 'first_name', None) == 'Martin':
            raise Http404()
        return super(PostUpdateView, self).post(request, *args, **kwargs)
```

### Slide 36
Making requests:
 - We want to implement a Stripe integration and send an email notification when we get a payment
 - We will use the official `stripe` Python wrapper
 - Fictional: We learned from their docs that we can call `stripe.Charge()` and it returns
   a dictionary with `{'id': 'charged'}"`
 - How can we avoid making actual HTTP requests to the Strpe API when we run our tests
   but still get the return dictionary because our view code depends on it?


### Slide 37
We will mock the stripe Python wrapper and create our own expected fake-response
```python
from django.core.mail import send_mail
from mock import patch
import stripe

class TestPaymentView:
    @patch('birdie.views.stripe')
    def test_payment(self, mock_stripe):
        mock_stripe.Charge.return_value = {'id': '234'}
        req = RequestFactory().post('/', data={'token': '123'})
        resp = views.PaymentView.as_view()(req)
        assert resp.status_code == 302, 'Should redirect to success_url'
        assert len(mail.outbox) == 1, 'Should send an email'

```

### Slide 38
Implement your view
```python
views.py
from django.core.mail import send_mail
import stripe
...
class PaymentView(View):
    def post(self, request, *args, **kwargs):
        charge = stripe.Charge.create(
            amount=100,
            currency='sgd',
            description='',
            token=request.POST.get('token'),
        )
        send_mail(
            'Payment received',
            'Charge {} succeeded!'.format(charge['id']),
            'server@example.com',
            ['admin@example.com', ],
        )
        return redirect('/')
```

### Slide 39
You can run specific tests like so
```bash
py.test birdie/tests/test_views.py::TestAdminView::test_superuser
```

You can put breakpoints into your tests like so:
```bash
pytest.set_trace()
```

### Slide 40
To be continued:
 - Testing Templatetags
 - Testing Django Management Commands
 - Testing with Sessions
 - Testing with Files
 - Testing Django Rest Framework APIViews
 - Running Tests in Parallel

### Slide 41
Thank you! Ask me anything!
 - Facebook: Martin Brochhaus
 - Twitter: [@mbrochh](https://twitter.com/mbrochh)
 - LinkedIn: [mbrochh](https://www.linkedin.com/in/mbrochh/)