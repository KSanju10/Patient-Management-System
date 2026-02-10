from fastapi import FastAPI, Path , HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field,computed_field
from typing import Annotated,Literal,Optional

import json

app=FastAPI()

class Patient(BaseModel):
    
    id:Annotated[str,Field(...,description="ID of the patient",example=["P001"])]
    name:Annotated[str,Field(...,description="Name of the patient")]
    city:Annotated[str,Field(...,description="City of the patient")]
    age:Annotated[int,Field(...,description="Age of the patient",gt=0,lt=120)]
    gender:Annotated[Literal['Male','Female','Other'],Field(...,description="Gender of the patient")]
    height:Annotated[float,Field(...,description="Height of the patient in meters",gt=0)]
    weight:Annotated[float,Field(...,description="Weight of the patient in kgs",gt=0)]
    
    @computed_field
    @property
    def bmi(self)->float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self)->str:
        if self.bmi<18.5:
            return "Underweight"
        elif 18.5<=self.bmi<25:
            return "Normal weight"
        elif 25<=self.bmi<30:
            return "Overweight"
        else:
            return "Obese"
    
    
class PatientUpdate(BaseModel):
    
    name: Annotated[Optional[str], Field(default=None, description="Name of the patient")]
    city: Annotated[Optional[str], Field(default=None, description="City of the patient")]
    age: Annotated[Optional[int], Field(default=None, description="Age of the patient", gt=0, lt=120)]
    gender: Annotated[Optional[Literal['Male','Female','Other']], Field(default=None, description="Gender of the patient")]
    height: Annotated[Optional[float], Field(default=None, description="Height of the patient in meters", gt=0)]
    weight: Annotated[Optional[float], Field(default=None, description="Weight of the patient in kgs", gt=0)]
    
    
def load_data():
    with open('patients.json','r') as f:
        data =json.load(f)
        
    return data

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)
    
    

@app.get("/")
# async def root():
def hello():
    return {"message": "Patient Management System API "}

@app.get("/about")
def about():
    return {"message": "A fully Functional API to manage your patient records."}

@app.get("/view")
def view():
    data=load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id:str=Path(...,description="The ID of the patient tin the DB ",example="P001")):
    data=load_data()
    
    if patient_id in data:
        return data[patient_id]
    # return {"error": "Patient not found"}
    raise HTTPException(status_code=404, detail="Patient not found")
    
@app.get("/sort")
def sort_patients(sort_by:str= Query(...,description="Sort on the bases of height, weight or bmi"), order:str=Query ('asc',description="sort in asc or desc order")):
    
    data = load_data()

    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field. Select from {valid_fields}")

    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order. Select between 'asc' and 'desc'")

    # compute bmi if needed
    enriched_data = []
    for pid, info in data.items():
        info_with_id = {**info, 'id': pid}
        patient_obj = Patient(**info_with_id)
        enriched_data.append(patient_obj.model_dump())

    reverse = True if order == "desc" else False
    sorted_data = sorted(enriched_data, key=lambda x: x.get(sort_by, 0), reverse=reverse)

    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    
    #load existing data
    data=load_data()
    
    #check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    
    #add new patient to data
    data[patient.id]=patient.model_dump(exclude=['id'])
    
    #save into the json file
    save_data(data)
    
    return JSONResponse(status_code=201,content={"message": "Patient created successfully"})
    

@app.put('/edit/{patient_id}')
def update_patient(patient_id:str, patient_update:PatientUpdate):
    
    data=load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient_info=data[patient_id]
    
    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    
    for key, value in updated_patient_info.items():
        existing_patient_info[key]=value
        
    # existing_patient_info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id']=patient_id
    patient_pydantic_obj=Patient(**existing_patient_info)
    
    # -> pydantic object -> dict -> save into json file
    data[patient_id]= patient_pydantic_obj.model_dump(exclude=['id'])
    
    # save data
    save_data(data)
    
    return JSONResponse(status_code=200,content={"message": "Patient updated successfully"})


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    #load data
    data=load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    del data[patient_id]
    
    save_data(data)
    
    return JSONResponse(status_code=200,content={"message": "Patient deleted successfully"})
