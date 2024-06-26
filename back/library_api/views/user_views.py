from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.http import HttpResponseForbidden, JsonResponse
from library_api.repositories.user_repository import UserRepository
from library_api.serializers.user_serializer import UserSerializer
from library_project.settings import SECRET_KEY
import jwt
import bcrypt

@csrf_exempt
def user_register(request):

    """
    Registers a new user.

    Method: POST
    Body: JSON containing 'email', 'username', and 'password'

    Returns:
        201: User created successfully
        400: User creation failed (e.g., email already exists or invalid JSON)
        405: Invalid request method
        500: Internal server error
    """

    if request.method == 'POST':
        try:
            data = UserSerializer.deserialize(request.body.decode('utf-8'))
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')

            user_repository = UserRepository()
            user_created = user_repository.create_user(email, username, password)

            if user_created:
                return JsonResponse({'message': 'User created successfully'}, status=201)
            else:
                return JsonResponse({'message': 'User creation failed: Email already exists'}, status=400)

        except ValueError:
            return JsonResponse({'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@csrf_exempt
def user_login(request):

    """
    Logs in a user.

    Method: POST
    Body: JSON containing 'email' and 'password'

    Returns:
        200: JWT token
        400: Invalid JSON
        403: Invalid credentials
        405: Invalid request method
        500: Internal server error
    """

    if request.method == 'POST':
        try:
            data = UserSerializer.deserialize(request.body.decode('utf-8'))
            email = data.get('email')
            password = data.get('password')

            user_repo = UserRepository()
            user_data = user_repo.get_user_by_email(email)

            if user_data:
                stored_password = user_data.get('password')
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    payload = {
                        '_id': str(user_data.get('_id')),
                        'exp': datetime.utcnow() + timedelta(days=1)  # Token expiration time
                    }
                    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
                    return JsonResponse({'token': token}, status=200)
                else:
                    return HttpResponseForbidden('Invalid credentials')
            else:
                return HttpResponseForbidden('Invalid credentials')
        except ValueError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def user_delete(request):

    """
    Deletes a user.

    Method: DELETE
    Header: Authorization token

    Returns:
        200: User deleted successfully
        403: User not found or token invalid
        405: Invalid request method
    """

    if request.method == 'DELETE':
        token = request.headers.get('Authorization').split(' ')[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            _id = payload['_id']
            user_repo = UserRepository()
            user_data = user_repo.get_user_by_id(_id)
            
            if user_data:
                user_repo.delete_user(_id)
                return JsonResponse({'message': 'User deleted successfully'})
            else:
                return HttpResponseForbidden('User not found')
        except jwt.ExpiredSignatureError:
            return HttpResponseForbidden('Token expired')
        except jwt.InvalidTokenError:
            return HttpResponseForbidden('Invalid token')

@csrf_exempt
def user_update(request):

    """
    Updates a user's information.

    Method: PUT
    Header: Authorization token
    Body: JSON containing 'username', 'password', 'bookshelf', and/or 'publishies'

    Returns:
        200: User updated successfully
        403: User not found or token invalid
        405: Invalid request method
    """

    if request.method == 'PUT':
        token = request.headers.get('Authorization').split(' ')[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            _id = payload['_id']
            user_repo = UserRepository()
            user_data = user_repo.get_user_by_id(_id)
            
            if user_data:
                data = UserSerializer.deserialize(request.body.decode('utf-8'))
                new_username = data.get('username')
                new_password = data.get('password')
                new_bookshelf = data.get('bookshelf')
                new_publishies = data.get('publishies')

                if new_username:
                    user_data['username'] = new_username
                if new_password:
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    user_data['password'] = hashed_password.decode('utf-8')
                if new_bookshelf:
                    user_data['bookshelf'] = new_bookshelf
                if new_publishies:
                    user_data['publishies'] = new_publishies

                user_repo.update_user(_id, user_data)
                return JsonResponse({'message': 'User updated successfully'})
            else:
                return HttpResponseForbidden('User not found')
        except jwt.ExpiredSignatureError:
            return HttpResponseForbidden('Token expired')
        except jwt.InvalidTokenError:
            return HttpResponseForbidden('Invalid token')

@csrf_exempt
def user_info(request):

    """
    Retrieves a user's information.

    Method: GET
    Header: Authorization token

    Returns:
        200: User information
        403: User not found or token invalid
        405: Invalid request method
    """

    if request.method == 'GET':
        token = request.headers.get('Authorization').split(' ')[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            _id = payload['_id']
            user_data = UserRepository().get_user_by_id(_id)

            if user_data:
                user_data = UserSerializer.sanitize(user_data)
                user_data['_id'] = str(user_data['_id'])
                return JsonResponse(user_data)
            else:
                return HttpResponseForbidden('User not found')
        except jwt.ExpiredSignatureError:
            return HttpResponseForbidden('Token expired')
        except jwt.InvalidTokenError:
            return HttpResponseForbidden('Invalid token')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def user_open_info(request, _id):
    
    """
    Get user information by user ID.

    Args:
        request (HttpRequest): The request object.
        _id (str): The user ID.

    Returns:
        JsonResponse: User information JSON response.
        HttpResponseForbidden: Forbidden response if user not found or token expired/invalid.
    """
     
    if request.method == 'GET':
        try:
            user_data = UserRepository().get_user_by_id(_id)

            if user_data:
                user_data = UserSerializer.sanitize(user_data)
                user_data['_id'] = str(user_data['_id'])
                return JsonResponse(user_data)
            else:
                return HttpResponseForbidden('User not found')
        except jwt.ExpiredSignatureError:
            return HttpResponseForbidden('Token expired')
        except jwt.InvalidTokenError:
            return HttpResponseForbidden('Invalid token')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)