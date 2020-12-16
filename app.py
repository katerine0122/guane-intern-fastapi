from typing import Optional
import databases, sqlalchemy, datetime, uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List


DATABASE_URL = "postgresql://usertest:123456@127.0.0.1:5432/dbtest"
database = databases.Database(DATABASE_URL)
metadata =sqlalchemy.MetaData()

dogs = sqlalchemy.Table(
    "dogs",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("picture", sqlalchemy.String),
    sqlalchemy.Column("create_date", sqlalchemy.String),
    sqlalchemy.Column("is_adopted", sqlalchemy.Boolean)
)

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)


class DogList(BaseModel):
    id :str
    name: str
    picture: str
    create_date: str
    is_adopted: bool

class DogRecord(BaseModel):
    name:       str  = Field(..., base ="name_dog")
    picture:    str  = Field(..., base ="https://dog.ceo/api/breeds/image/random")
    is_adopted: bool = Field(..., base ="True")

class DogUpdate(BaseModel):
    name:        str = Field(..., base ="enter name dog")
    picture:     str = Field(..., base ="https://dog.ceo/api/breeds/image/random")
    is_adopted: bool = Field(..., base ="True")

class DogDelete(BaseModel):
    name:        str = Field(..., base="enter name dog")


app= FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()



@app.get("/")
def index():
    return {"FastAPI test"}

#GET -> /api/dogs
@app.get("/dogs", response_model=List[DogList])
async def find_all_dogs():
    query = dogs.select()
    return await database.fetch_all(query)

#GET -> /api/dogs/{name}
@app.get("/dogs/{name}", response_model=DogList)
async def find_dog_by_name(name: str):
    query = dogs.select().where(dogs.c.name == name)
    return await database.fetch_one(query)

#GET -> /api/dogs/is_adopted
@app.get("/dogs/is_adopted/{is_adopted}", response_model=List[DogList])
async def find_dogs_adopted(is_adopted: bool):
    query = dogs.select().where(dogs.c.is_adopted == is_adopted)
    return await database.fetch_all(query)

#POST -> /api/dogs/{name}
@app.post("/dogs", response_model=DogList)
async def register_dog(dog: DogRecord):
    getID   = str(uuid.uuid1())
    getDate = str(datetime.datetime.now())
    getbreed = str("https://dog.ceo/api/breeds/image/random")
    query   = dogs.insert().values(
        id          = getID,
        name        = dog.name,
        picture     = getbreed,
        create_date = getDate,
        is_adopted  = dog.is_adopted
    )

    await database.execute(query)
    return {
        "id": getID,
        **dog.dict(),
        "create_date" : getDate,
    }

#PUT -> /api/dogs/{name}
@app.put("/dogs", response_model=DogList)
async def update_dog(dog: DogUpdate):
    getDate = str(datetime.datetime.now())
    query   = dogs.update().\
        where(dogs.c.name == dog.name).\
        values(
            name        = dog.name,
            picture     = dog.picture,
            create_date = getDate,
            is_adopted  = dog.is_adopted
        )
    await database.execute(query)
    return await find_dog_by_name(dog.name)

#DELETE -> /api/dogs/{name}
@app.delete("/dogs/{name}")
async def delete_dog_by_name(dog:DogDelete):
    query = dogs.delete().where(dogs.c.name == dog.name)
    await database.execute(query)

    return {
        "status" : True,
        "message": f"The dog named <<{dog.name}>> has been eliminated"
    }

