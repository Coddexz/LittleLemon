# Little Lemon Restaruant API

## Description
Little Lemon Restaurant API is a web API that facilitates the organization and management of restaurant operations. The API provides tools to manage delivery crew and managers, create and update menus, food categories, assign orders, and mark their status. Additionally, the API allows customers to create accounts, log in, browse menus and categories, add menu items to the cart, place orders, and view their order history. Access to the API is divided into groups with different levels of access. The API uses various utilities such as sorting, paging, filtering, and throttling.

## Technologies
Little Lemon Restaurant API was built using the Django framework, Django REST framework, Djoser, and Pipenv.

## Design Choices
The project's goals were set by Meta, and the API was built from the ground up. The API was designed using different types of views, such as generics, class-based viewsets, and function-based views. The authentication and authorization system was designed with different levels of access depending on user roles. The API uses default User and Group models, as well as models created specifically for this project. To access all endpoints, users need to change their roles.

To optimize performance, the API implements throttling, filtering, ordering, and paging. These features are especially useful for frequently used endpoints such as menu-items and orders.

Pipenv was used to manage dependencies and create the virtual environment. SQLite3 was used as the default database for Django projects.

## Instalation and usage
To use Little Lemon Restaurant API, follow these steps:
1. Navigate to the project's directory  
`cd LittleLemon`
2. Activate the virtual environment  
`pipenv shell`
3. Install all dependencies  
`pipenv install`
4. Apply database migrations  
`python manage.py makemigrations`
`python manage.py migrate`
5. Run the server  
`python manage.py runserver`

Endpoints:
- '**/auth/users**'
- '**/auth/users/users/me**'
- '**/auth/token/login**'
- '**/api/menu-items**'
- '**/api/menu-items/{menuItem}**'
- '**/api/groups/manager/users**'
- '**/api/groups/{group}/users/{userId}**'
- '**/api/cart/menu-items**'
- '**/api/orders**'
- '**/api/orders/{orderId}**'

All credentials are provided in LittleLemon/notes.txt.
