from django.shortcuts import redirect, render
from django.http import HttpResponse

from django.contrib.auth.models import User

from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site

from django.contrib import messages
from job_wala import settings
from django.core.mail import send_mail,EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_str,force_bytes
from . tokens import generate_token


# Create your views here.

# @login_required(login_url='login')

def home(request):
    return render(request,"authentication/base.html")



def signup(request):

    

    if request.method=="POST":
        
        username=request.POST.get('username')
        fname=request.POST.get('fname')
        lname=request.POST.get('lname')
        email=request.POST.get('email')
        pass2=request.POST.get('pass2')
        pass1=request.POST.get('pass1')

       

        if User.objects.filter(username=username):
            messages.error(request,"username is already register ! please try some other username")

        if User.objects.filter(email=email):
            messages.error(request,"email already register!")
        
        if len(username)>10:
            messages.error(request,"username must be under 10 character")

        if pass1!=pass2:
            messages.error(request,"password doesn't match ")

        

        if not username.isalnum:
            messages.error(request,"usename must be alpha numeric")
            return redirect('home')
        
    


        

        myuser = User.objects.create_user(username, email, pass1)
      
        myuser.first_name=fname
        myuser.last_name=lname
        myuser.is_active=False

        

        myuser.save()

        messages.success(request,"your account has been successfully created")


        #welcome message

        subject="welcome to job wala"
        message="hello"+myuser.first_name

        from_email=settings.EMAIL_HOST_USER
        to_list=[myuser.email]
        send_mail(subject,message,from_email,to_list,fail_silently=True)


        #Email address confirmation email

        current_site=get_current_site(request)
        email_subject="confirm your email @jobwala - login!!"
        dict={
            'name': myuser.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token().make_token(myuser)
        }
        message2=render_to_string('authentication\email_confirmation.html',dict)
        email=EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],


        )

        email.fail_silently=True
        email.send()



        return redirect('/')


    return render(request,"authentication/signup.html")


def signin(request):
    
    if request.method=="POST":
        username=request.POST.get('username')
        pass1=request.POST.get('pass1')
        
        user=authenticate(username=username,password=pass1)
        
        if user is not None:
            login(request,user)
            fname=user.first_name
            return render(request,"authentication/base.html",{'fname':fname})

        else:
            messages.error(request,"Bad credentials")
            return redirect('home')



    return render(request,"authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request,"logged out successfully")
    return redirect('home')

def activate(request,uidb64,token):

    try:

        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser=User.objects.get(pk=uid)

    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser=None

    if myuser is not None and generate_token().check_token(myuser,token):
        myuser.is_active=True
        myuser.save()
        login(request,myuser)

        return redirect("/")
    
    else:
        return render(request,'authentication\activation_failed.html')