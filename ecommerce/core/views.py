from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render,redirect
from core.forms import *
from core.models import *
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View,TemplateView,ListView
from .helpers import send_forget_password_mail
from django.contrib import messages
import uuid
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))


def signin_required(fn):
    def inner(request,*args,**kwargs):
        if request.user.is_authenticated:
            return fn(request,*args,**kwargs)
        else:
            messages.error(request,"Unsuccessful...!Login Required")
            return redirect('user_login')
    return inner

dec = [signin_required,never_cache]
# Create your views here.
def index(request):
    products = Product.objects.all()
    paginator = Paginator(products,4)
    page_number = request.GET.get('page')
    pages = paginator.get_page(page_number)
    return render(request,'core/indexx.html',{'products':pages})
    

@method_decorator(dec,name='dispatch')
class Orderlist(View):
    def get(self,request):
        if Order.objects.filter(user=request.user, ordered=False).exists():
            order = Order.objects.get(user=request.user, ordered=False)
            return render(request, "core/orderlist(2).html", {"order": order})
        else:
            return render(request, "core/orderlist(2).html", {"message": "Your Cart is Empty"})
        
@method_decorator(dec,name='dispatch')
class Add_Product(View):
    def get(self,request):
        form = ProductForm()
        return render(request, "core/add_product.html", {"form": form})
    def post(self,request):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            print("True")
            form.save()
            print("Data Saved Successfully")
            messages.success(request, "Product Added Successfully")
            return redirect("/")
        else:
            print("Not Working")
            messages.info("Product is not Added, Try Again")
            return render(request, "core/add_product.html", {"form": form})


class Product_Desc(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)
        return render(request, "core/product_desc2.html", {"product": product})
    
@method_decorator(dec,name='dispatch')
class Add_To_Cart(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)

    # Create Order item
        order_item, created = OrderItem.objects.get_or_create(product=product,user=request.user,ordered=False,)

    # Get Query set of Order Object of Particular User
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(product__pk=pk).exists():
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "Added Quantity Item")
                return redirect("product_desc", pk=pk)
            else:
                order.items.add(order_item)
                messages.info(request, "Item added to Cart")
                return redirect("product_desc", pk=pk)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "Item added to Cart")
            return redirect("index")
        
@method_decorator(dec,name='dispatch')  
class Add_item(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)

    # Create Order item
        order_item, created = OrderItem.objects.get_or_create(product=product,user=request.user,ordered=False,)

    # Get Query set of Order Object of Particular User
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(product__pk=pk).exists():
                if order_item.quantity < product.product_available_count:
                    order_item.quantity += 1
                    order_item.save()
                    messages.info(request, "Added Quantity Item")
                    return redirect("orderlist")
                else:
                    messages.info(request, "Sorry! Product is out of Stock")
                    return redirect("orderlist")
            else:
                order.items.add(order_item)
                messages.info(request, "Item added to Cart")
                return redirect("product_desc", pk=pk)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "Item added to Cart")
            return redirect("product_desc", pk=pk) 
        
def remove_item(request, pk):
    item = get_object_or_404(Product, pk=pk)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item = OrderItem.objects.filter(
                product=item,
                user=request.user,
                ordered=False,
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Item quantity was updated")
            return redirect("orderlist")
        else:
            messages.info(request, "This item is not in your cart")
            return redirect("orderlist")
    else:
        messages.info(request, "You Do not have any Order")
        return redirect("orderlist")

def checkout_page(request):
    if CheckoutAddress.objects.filter(user=request.user).exists():
        return render(request, "core/checkout_address.html", {"payment_allow": "allow"})
    if request.method == "POST":
        print("Saving must start")
        form = CheckoutForm(request.POST)
        if form.is_valid():
            street_address = form.cleaned_data.get("street_address")
            apartment_address = form.cleaned_data.get("apartment_address")
            country = form.cleaned_data.get("country")
            zip_code = form.cleaned_data.get("zip")

            checkout_address = CheckoutAddress(
                user=request.user,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zip_code=zip_code,
            )
            checkout_address.save()
            print("It should render the summary page")
            return render(
                request, "core/checkout_address.html", {"payment_allow": "allow"}
            )

    else:
        form = CheckoutForm()
        return render(request, "core/checkout_address.html", {"form": form})  

@login_required
def payment(request):
    try:
        order = Order.objects.get(user=request.user, ordered=False)
        address = CheckoutAddress.objects.get(user=request.user)
        order_amount = order.get_total_price()
        order_currency = "INR"
        order_receipt = order.order_id
        notes = {
            "street_address": address.street_address,
            "apartment_address": address.apartment_address,
            "country": address.country.name,
            "zip": address.zip_code,
        }
        razorpay_order = razorpay_client.order.create(
            dict(
                amount=order_amount * 100,
                currency=order_currency,
                receipt=order_receipt,
                notes=notes,
                payment_capture="0",
            )
        )
        print(razorpay_order["id"])
        order.razorpay_order_id = razorpay_order["id"]
        order.save()
        print("It should render the summary page")

        return render(
            request,
            "core/paymentsummaryrazorpay.html",
            {
                "order": order,
                "order_id": razorpay_order["id"],
                "orderId": order.order_id,
                "final_price": order_amount,
                "razorpay_merchant_id": settings.RAZORPAY_ID,
            },
        )

    except Order.DoesNotExist:
        print("Order not found")
        return HttpResponse("404 Error")
    
def render_pdf_view(request):
    order_db = Order.objects.get(razorpay_order_id=order_id)
    checkout_address = CheckoutAddress.objects.get(user=request.user)
    amount = order_db.get_total_price()
    amount = amount * 100
    payment_id = order_db.razorpay_payment_id
    payment_status = razorpay_client.payment.capture(payment_id, amount)
    template_path = 'invoice/invoice.html'
    context = {
        "order":order_db,"payment_status":payment_status,"checkout_address":checkout_address
    }

    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@csrf_exempt
def handlerequest(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get("razorpay_payment_id", "")
            order_id = request.POST.get("razorpay_order_id", "")
            signature = request.POST.get("razorpay_signature", "")
            print(payment_id, order_id, signature)
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            try:
                order_db = Order.objects.get(razorpay_order_id=order_id)
                print("Order Found")
            except:
                print("Order Not found")
                return HttpResponse("505 Not Found")
            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()
            print("Working............")
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            if result != None:
                print("Working Final Fine............")
                amount = order_db.get_total_price()
                amount = amount * 100  # we have to pass in paisa
                payment_status = razorpay_client.payment.capture(payment_id, amount)
                if payment_status is not None:
                    print(payment_status)
                    order_db.ordered = True
                    order_db.save()
                    print("Payment Success")
                    checkout_address = CheckoutAddress.objects.get(user=request.user)
                    request.session[
                        "order_complete"
                    ] = "Your Order is Successfully Placed, You will receive your order within 5-7 working days"
                    return render(request, "invoice/invoice.html",{"order":order_db,"payment_status":payment_status,"checkout_address":checkout_address})
                else:
                    print("Payment Failed")
                    order_db.ordered = False
                    order_db.save()
                    request.session[
                        "order_failed"
                    ] = "Unfortunately your order could not be placed, try again!"
                    return redirect("/")
            else:
                order_db.ordered = False
                order_db.save()
                return render(request, "core/paymentfailed.html")
        except:
            return HttpResponse("Error Occured")
        
@method_decorator(dec,name='dispatch')       
class Invoice(View):
    def get(self,request):
        return render(request, "invoice/invoice.html")
    
@method_decorator(dec,name='dispatch')       
class OrderListView(View):
    def get(self,request,*args,**kwargs):
        if request.user.is_authenticated:                                   
            user = request.user                                             
            details = Order.objects.filter(user=user)                    
            return render(request,'core/myorders.html',{'details':details})       
        else:                                                                
             return render(request,'core/myorders.html')
         
def cancelorder(request,id):
    ord = Order.objects.get(id=id)
    ord.status='Cancel'
    ord.save()
    messages.error(request,'Order Cancelled')
    return redirect('orders')

class About(TemplateView):
    template_name = 'core/about.html'
    
class Contact(TemplateView):
    template_name = 'core/contact.html'
    

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET.get('keyword') or ''
        if keyword:
            products = Product.objects.filter(name__icontains=keyword)
            return render(request,'core/indexx.html',{'products':products})
        else:
            
            return redirect('index')
            
