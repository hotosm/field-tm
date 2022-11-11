from email.mime import image
from fastapi import FastAPI, Query, Path, Body, Cookie, Header, Form, File, UploadFile, HTTPException, status, Depends, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from enum import Enum
from pydantic import BaseModel, Required, Field
from typing import Union, List, Dict

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Order matters. For example /users/me must be declared before /users/{user_id},
# because me could be considerd {user_id}. If a route is declared 2x, the first will always be used.

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "about": "Takes parameter with automatic type check",
        "item": items[item_id]}

class AbcCode(str, Enum):
    a = "Alfa"
    b = "Bravo"
    c = "Charlie"

@app.get("/code/{letter}")
async def get_code(letter: AbcCode):
    return {"item_id": letter, "about": "Takes enum parameter."}

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path, "about": "With path check."}

# The query is the set of key-value pairs that go after the ? in a URL, separated by & characters.
# Queries have defaults and can be optional (set = to None).

# example: http://127.0.0.1:8000/items IS THE SAME AS: http://127.0.0.1:8000/items/?skip=0&limit=10
# returns: [{"item_name":"Foo"},{"item_name":"Bar"},{"item_name":"Baz"}]

# example: http://127.0.0.1:8000/items/?skip=0&limit=2 IS THE SAME AS: http://127.0.0.1:8000/items/?limit=2
# returns: [{"item_name":"Foo"},{"item_name":"Bar"}]

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10, index: int = None):
    if index:
        return fake_items_db[index] # Note: 0 evaluates as None so can't get first index
    return fake_items_db[skip : skip + limit]

# To make a query required, give no default value

# bool types can be:
# http://127.0.0.1:8000/truth?tell_me=1
# http://127.0.0.1:8000/truth?tell_me=True
# http://127.0.0.1:8000/truth?tell_me=true # or any other case variation, ex TRUE
# http://127.0.0.1:8000/truth?tell_me=on
# http://127.0.0.1:8000/truth?tell_me=yes

@app.get("/truth/")
async def is_true(tell_me: bool):
    if tell_me:
        return {"message": "Yes Indeedy!!"}
    return {"message": "Not so much!!"}

# Complex types that inherit from pydantic BaseModel will be checked and automatically jsonified.
# Attributes with default values are not required. Parameters with None are optional.
# FastApi will assume that Pydantic models are part of the request body.
# typing List or Set can be used for list or set type validation. HttpUrl can be used for valid urls.
# Field can be used to add validation to attributes.

class Image(BaseModel):
    url: str = Field(example="http://example.com/baz.jpg") # used for docs
    name: str

class Heart(BaseModel):
    rate: int 
    healthy: bool
    broken: bool = False
    loves: List[str] = []
    description: Union[str, None] = Field(
        default=None, title="The description of the item", max_length=300
    )
    image: Union[Image, None] = None

    # To give an example in the docs
    class Config:
        schema_extra = {
            "example": {
                "rate": "120",
                "healthy": True,
                "broken": True,
                "loves": {"sloths","AI","soft things"},
                "description": "blond beauty",
                "image": {
                    "url": "http://example.com/baz.jpg",
                    "name": "The Foo live"
                }

            }
        }

# just to show another metadata/documentation example with multiple examples
class Lung(BaseModel):
    image: Image = Body(
        examples={
            "normal": {
                "url": "http://example.com/baz.jpg",
                "name": "The Foo live"
            },
            "smoker": {
                "url": "http://example.com/baz.jpg",
                "name": "The Foo dead"
            }
        },
    )

# other built in datatypes: 
# UUID, 
# dattime.datetime, 2008-09-15T15:53:00+05:00
# datetime.date, 2008-09-15
# datetime.time, 14:23:55.003
# datetime.timedelta,  float of total seconds
# frozenset, In requests, a list will be read, eliminating duplicates and converting it to a set.
#   In responses, the set will be converted to a list.
#   The generated schema will specify that the set values are unique (using JSON Schema's uniqueItems).
# bytes
# Decimal, handled as float
# EmailStr

@app.post("/hearts/", response_model=Heart)
async def create_item(heart: Heart):
    if heart.broken:
        return {"message": "Yesterday.... All my troubles seemed so far away... Now it seems as though they're here to stay... Oh, I believe in yesterday..."}
    return heart

# Can use in and out and response type to do validation or hide data
# It is recommended to do it this way rather than exclude because it will be better documented that way.
# Example:
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Union[str, None] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    email: EmailStr
    full_name: Union[str, None] = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Union[str, None] = None

def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password

user_id_generator = 0
users = {int, UserInDB}

def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
   
    # you can turn a model into a dict with .dict() and pass it into a constructor to create an instance
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)

    user_dict = user_in.dict()
    a_user = UserInDB(**user_dict)

    same_use = UserInDB(**user_in.dict())

    another_copy = UserInDB(
        username = user_dict["username"],
        password = user_dict["password"],
        email = user_dict["email"],
        full_name = user_dict["full_name"],
    )

    #in case you have a datastring that can't be saved into the database for example, similar to json.dumps()
    json_compatible_item_data = jsonable_encoder(user_in)

    print("User saved! ..not really")
    users[users_id_generator] = a_user
    users_id_generator = users_id_generator+1
    return user_in_db

@app.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)

    return user_saved

@app.patch("/user/{user_id}", response_model=UserOut)
async def update_item(user_id: str, user: UserIn):
    stored_user_data = user[user_id]
    stored_user_model = UserInDB(**stored_user_data)
    update_data = user.dict(exclude_unset=True)
    updated_user = stored_user_model.copy(update=update_data)
    user[user_id] = jsonable_encoder(updated_user)
    return updated_user

# A better way to do the above with less duplicaiton and chance for error
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Union[str, None] = None

class UserIn(UserBase):
    password: str

class UserOut(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

# Notes on Union
class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type = "car"


class PlaneItem(BaseItem):
    type = "plane"
    size: int

@app.get("/items/{item_id}", response_model=Union[PlaneItem, CarItem])
async def read_item(item_id: str):
    return items[item_id]

    # Can also use @app.get("/items/", response_model=List[Item])

# to not return parameters/not passed in response: use response_model_exclude_unset=True
# For example: @app.get("/items/{item_id}", response_model=Item, response_model_exclude_unset=True)
# This is smart enough to know that a value passed in WAS NOT THE DEFAULT
# you can also use response_model_include and response_model_exclude to remove some data from an output


# Some notes on validation:
# Use Union[str, None] to allow your editor to give you better support and detect errors.
# Query can be used to do additional validation (it needs to be imported).
# A parameter can also be made optional with = Query(default=None)

@app.get("/shortstring/")
async def read_items(q: Union[str, None] = Query(default=None, min_length=1, max_length=3)):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results

@app.get("/regex/")
async def regex_validation(
    q: Union[str, None] = Query(
        default=None, min_length=3, max_length=50, regex="^regex$"
    )
):
    return {"message": "^: starts with the following characters, doesn't have characters before. regex: has the exact value regex. $: ends there, doesn't have any more characters after fixedquery." }
   
# Not setting a default value, or setting the default to ... both make a value required
# if you need a none value, use Elipses

@app.get("/noneANDrequired/")
async def required_and_accepts_none(q: Union[str, None] = Query(default=..., min_length=3)):
    return q

# Required can also be set with Pydantic (must be imported)

@app.get("/required/")
async def required_w_pydantic(q: str = Query(default=Required, min_length=3)):
    return q

# Example of list (imported) of path operations: http://localhost:8000/multiple/?q=foo&q=bar
# Unless you use query, List will be interpreted as a request body.
# python list can also be used but there will be no type checking.
@app.get("/multiple/")
async def read_many(q: Union[List[str], None] = Query(default=["ho", "hum"])):
    query_items = {"q": q}
    return query_items

# Same idea with dict. Json will take a string key, but Pydantic will figure it out.
@app.post("/index-weights/")
async def create_index_weights(weights: Dict[int, float]):
    return weights

# More metadata:
# Note that those with no default value need to go first, but it doesn't matter to fast API. Or use first parameter *
@app.get("/metadata/{path}",
    summary="the summary",
    description="the description",
    deprecated=True
)
async def read_something_and_know_what_it_is(
    path: int = Path(title="The ID of the item to get. Greater to or equal to 1. You can also use gt (greater than) or le (less than or equal)", ge=1),
    q: Union[str, None] = Query(
        default=None,
        alias="item-query",
        title="Query string",
        description="Query string for the items to search in the database that have a good match",
        min_length=3,
        max_length=50,
        regex="^fixedquery$",
        deprecated=True,
        # include_in_schema=False # This would hide this route from documentation
    )
):
    return "la de da da"

@app.get("/route_description/", 
    summary="showing some metadata functionality",
    response_description="a random string",)
async def route_description():
    """
    This can be markdown and will be used as the description in the interactive docs

    # Header 1
    ## Header 2
    """
    return "message"

# If you pass two body parameters, the request will expect a dict.
# Body can be used to make simple types expected in the body

@app.put("/hearts/")
async def in_love(h1: Heart, h2: Heart, importance: int = Body()):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results

# Body expected: {
#     "h1": {
#         ...
#     },
#     "h2": {
#         ...
#     },
#     "importance": 1
# }

# By default one parameter will not have a key. To make it have a key, use h1: Heart = Body(embed=True)

@app.get("/cookie/")
async def read_items(ads_id: Union[str, None] = Cookie(default=None)):
    return {"ads_id": ads_id}

@app.get("/items-header/{item_id}")
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}

# Header parameters include change from - to _ for python, example: user-agent to user_agent
@app.get("/header/")
async def read_items(user_agent: Union[str, None] = Header(default=None)):
    return {"User-Agent": user_agent}

@app.get("/xtoken/")
async def read_items(x_token: Union[List[str], None] = Header(default=None)):
    return {"X-Token values": x_token}

# To accept form data. You can't accept both form data and body (part of the HTTP protocol)
@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    return {"username": username}

# Files will be uploaded as form data, 
# File: recieving the content as bytes will store the whole contents in memory and should only be used for small files
# UploadFile: uses a "spooled" file, which will store in memory up to a size limit and then will store in disk,
#   allows you to access metadata
#   has file-like asyn interface
#   attributes: filename, content_type, file
#   async methods: write(data), read(size), seek(offset), close() Example: contents = await myfile.read()
# If you ware in a def path operation function, can access directly (contents = myfile.file.read()) 

@app.post("/files/")
async def create_file(
    file: Union[bytes, None] = File(default=None), 
    fileb: UploadFile = File(description="A file with some extra metadata"), 
    token: str = Form()
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

# a list: async def create_files(files: List[bytes] = File()):

# Example form for multiple files
# <body>
# <form action="/files/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input type="submit">
# </form>
# <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input type="submit">
# </form>
# </body>

# Status code:
# Fast API has some codes: Example: status_code=status.HTTP_201_CREATED
# Send with: @app.post("/items/", status_code=201)

# 100 and above are for "Information". You rarely use them directly. Responses with these status codes cannot have a body.
# 200 and above are for "Successful" responses. These are the ones you would use the most.
#   200 is the default status code, which means everything was "OK".
#   Another example would be 201, "Created". It is commonly used after creating a new record in the database.
#   A special case is 204, "No Content". This response is used when there is no content to return to the client, and so the response must not have a body.
# 300 and above are for "Redirection". Responses with these status codes may or may not have a body, except for 304, "Not Modified", which must not have one.
# 400 and above are for "Client error" responses. These are the second type you would probably use the most.
#   An example is 404, for a "Not Found" response.
#   For generic errors from the client, you can just use 400.
# 500 and above are for server errors. You almost never use them directly. When something goes wrong at some part in your application code, or server, it will automatically return one of these status codes.

# To handle an exception globally:
class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.get("/unicorns/{name}")
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}

# Dependency injection/path operation functions example
# Dependencies must be callable, which include Python classes with an __init__
async def common_parameters(
    q: Union[str, None] = None, skip: int = 0, limit: int = 100
):
    return {"q": q, "skip": skip, "limit": limit}

class CommonQueryParams:
    def __init__(self, q: Union[str, None] = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


@app.get("/injection/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons

@app.get("/injection2/")
async def read_items(commons: CommonQueryParams = Depends(CommonQueryParams)):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip : commons.skip + commons.limit]
    response.update({"items": items})
    return response

# Could be written but with less editor support: async def read_items(commons=Depends(CommonQueryParams))
# commons: CommonQueryParams = Depends(CommonQueryParams) can be shortened to: commons: CommonQueryParams = Depends()
# If a depends is used multiple times, the value will be cached. If you don't want that... 
async def needy_dependency(fresh_value: str = Depends(get_value, use_cache=False)):
    return {"fresh_value": fresh_value}

# These dependencies will be executed/solved the same way normal dependencies. 
# But their value (if they return any) won't be passed to your path operation function, so can be reused.
async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/verification_dependencies/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

# Global dependency, always checked
# app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])

# Only the code prior to and including the yield statement is executed before sending a response:
class DBSession:
    id: id = 0
    def close():
        pass

async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

# No HTTPExcerptions because yield is executed after the response is sent, so exception handlers will already have run

# Content Managers are anything that uses a with statement. Creating a dependency with yield makes it a content manger
# So, instead of the above you could do the python way of creating a content manager with __enter__ and __exit__
class MySuperContextManager:
    def __init__(self):
        self.db = DBSession()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


async def get_db():
    with MySuperContextManager() as db:
        yield db

# Send accepted response then do something the client doesn't need to wait for
def write_notification(email: str, message=""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}