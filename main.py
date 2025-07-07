from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List
import json, os

app = FastAPI()

class Tea(BaseModel):
    id: int
    name: str
    origin: str

@app.exception_handler(HTTPException)
async def custom_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail))}
    )


teas: List[Tea] = []

try:
    with open('database.txt', 'r') as file:

        data = json.load(file)
        if isinstance(data, list):
            teas = [Tea(**tea) for tea in data]
        else:
            teas = []
except (FileNotFoundError, json.JSONDecodeError):
    teas = []


@app.get('/')
def read_root():
    return {'message': 'Welcome to FastAPI'}


@app.get('/teas')
def get_teas():
    try:
        with open('database.txt', 'r') as file:
            teas = json.load(file)
            return{
                'message': f"{len(teas)} teas found.",
                'data': teas
            }
    except (FileNotFoundError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail='Database file not found or empty file found')


@app.get('/tea/{tea_id}')
def get_tea(tea_id: int):
    for index, tea in enumerate(teas):
        if tea.id == tea_id:
            return {
                'message': 'Tea found',
                'tea': tea
            }
    raise HTTPException(status_code=404, detail='Tea not found for the given id.')


@app.post('/add_tea')
def add_tea(tea: Tea):

    if any(existing_tea.id == tea.id for existing_tea in teas):
        raise HTTPException(status_code=409, detail={'message': f"Tea already exists with ID {tea.id}"})
    
    teas.append(tea)
    with open('database.txt', 'w') as file:
        json.dump([tea.model_dump() for tea in teas], file)
    return {
        'message': 'Tea successfully saved',
        'tea': tea
    }


@app.put('/update/{tea_id}')
def update_tea(tea_id: int, updated_tea: Tea):
    for index, tea in enumerate(teas):
        if tea.id == tea_id:
            teas[index] = updated_tea

            with open('database.txt', 'w') as file:
                json.dump([tea.model_dump() for tea in teas], file)
            return {
                'message': 'Tea successfully updated',
                'tea': updated_tea
            }
    raise HTTPException(status_code=404, detail='Tea not found with the given id.')


@app.delete('/delete/{tea_id}')
def delete_tea(tea_id: int):
    for index, tea in enumerate(teas):
        if tea.id == tea_id:
            deleted = teas.pop(index)

            with open('database.txt', 'w') as file:
                json.dump([tea.model_dump() for tea in teas] , file)

            return {
                'message': 'Tea deleted successfully',
                'deleted_tea': deleted
            }
    raise HTTPException(status_code=404, detail='Tea not found for the given id.')


@app.get('/download_file')
def download_tea_file():

    if not os.path.exists('database.txt'):
        raise HTTPException(status_code=404, detail='Database file not found')
    
    return FileResponse(
        path='database.txt',
        filename='database.txt',
        media_type='text/plain'
    )