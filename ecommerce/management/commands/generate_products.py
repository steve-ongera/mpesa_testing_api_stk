from django.core.management.base import BaseCommand
from ecommerce.models import Product
import random

class Command(BaseCommand):
    help = "Generate fake products"

    def handle(self, *args, **kwargs):
        product_names = [
            "Smartphone", "Laptop", "Tablet", "Smartwatch", "Bluetooth Speaker",
            "Wireless Earbuds", "Camera", "Keyboard", "Mouse", "Charger"
        ]
        
        descriptions = [
            "High quality and durable.", "Latest model with advanced features.",
            "Limited stock available.", "Popular choice among users.",
            "Now with enhanced battery life."
        ]
        
        for i in range(20):  # generate 20 products
            name = random.choice(product_names) + f" {random.randint(100, 999)}"
            price = round(random.uniform(1000.00, 50000.00), 2)
            description = random.choice(descriptions)
            
            Product.objects.create(name=name, price=price, description=description)
        
        self.stdout.write(self.style.SUCCESS("Successfully generated 20 products."))
