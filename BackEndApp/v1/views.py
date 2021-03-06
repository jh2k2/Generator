from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import sys
import os
import json
import importlib

sys.path.append("..")

from authv1.store import Store
from authv1.models import User
from DLMML.utils import json_to_dict
from DLMML.parser import *


@api_view(["POST"])
def generate(request):
    body_unicode = request.body.decode("utf-8")
    inputs_json = json.loads(body_unicode)
    inputs = json_to_dict.MakeDict(inputs_json).parse()

    lib = inputs.get("lib", "keras")
    lang = inputs.get("lang", "python")
    parser_path = "DLMML.parser." + lang + "." + lib + ".main"
    parser = importlib.import_module(parser_path)

    status, error = parser.generate_code(inputs)
    if status:
        print("Error", error)
        msg = error
        path = ""
    else:
        print("File generated")
        msg = "File Generated Successfully"
        path = "file:///" + os.getcwd() + os.sep + "test.py"

    return JsonResponse({"message": msg, "path": path})


@api_view(["POST"])
def train(request):
    try:
        os.system("gnome-terminal -e ./train.sh")
        msg = "Training started successfully"
    except Exception as e:
        msg = e
    return JsonResponse({"message": msg})


@api_view(["POST"])
def compile(request):
    try:
        body_unicode = request.body.decode("utf-8")
        inputs_json = json.loads(body_unicode)
        inputs = json_to_dict.MakeDict(inputs_json).parse()

        lib = inputs.get("lib", "keras")
        lang = inputs.get("lang", "python")
        test_path = "DLMML.parser." + lang + "." + lib + ".test_model"
        test_model = importlib.import_module(test_path)

        status, error = test_model.test_compile_model(inputs)
        print(status, error)
    except Exception as e:
        status, error = 1, e
    return JsonResponse({"status": status, "error": error})


@api_view(["POST"])
def get_all_projects(request):
    try:
        username = request.data.get("username")
        user = User(username=username, password=None)
        user = user.find()

        store_obj = Store(user)
        project_ids = store_obj.enlist()
        projects = []

        for id in project_ids:
            with open(store_obj.path + os.sep + id + os.sep + "meta.json", "r") as f:
                metadata = json.load(f)

            list_item = {id: metadata}
            projects.append(list_item)

        status, success, message = 200, True, "Projects Fetched"
    except Exception as e:
        status, success, message, projects = 500, False, str(e), ''
    return JsonResponse(
        {"success": success, "message": message, "projects": projects}, status=status
    )


@api_view(["POST"])
def get_project(request):
    try:
        username = request.data.get("username")
        user = User(username=username, password=None)
        user = user.find()

        store_obj = Store(user)
        project_id = request.data.get("project_id")
        if not store_obj.exist(project_id):
            raise Exception("No such project exists")
        project_dir = store_obj.path + os.sep + project_id

        with open(project_dir + os.sep + "layers.json", "r") as f:
            layers = json.load(f)

        # TODO: Write parser to convert this to required format (b2f)
        b2f_json = layers
        status, success, message = 200, True, "Layers Fetched"

    except Exception as e:
        status, success, message, b2f_json = 500, False, str(e), {}
    return JsonResponse(
        {"success": success, "message": message, "b2f_json": b2f_json}, status=status
    )


@api_view(["POST"])
def edit_project(request):
    try:
        username = request.data.get("username")
        user = User(username=username, password=None)
        user = user.find()

        project_id = request.data.get("project_id")
        project_name = request.data.get("project_name")
        data_dir = request.data.get("data_dir")
        output_file_name = request.data.get("output_file_name")

        store_obj = Store(user)
        if not store_obj.exist(project_id):
            raise Exception("No such project exists")
        project_dir = store_obj.path + os.sep + project_id

        with open(project_dir + os.sep + "meta.json", "r") as f:
            metadata = json.load(f)

        metadata["project_name"] = (
            project_name if project_name is not None else metadata["project_name"]
        )
        metadata["data_dir"] = (
            data_dir if data_dir is not None else metadata["data_dir"]
        )
        metadata["output_file_name"] = (
            output_file_name
            if output_file_name is not None
            else metadata["output_file_name"]
        )

        with open(project_dir + os.sep + "meta.json", "w") as f:
            json.dump(metadata, f)
        status, success, message = 200, True, "Project Updated Successfully"
    except Exception as e:
        status, success, message = 500, False, str(e)
    return JsonResponse({"success": success, "message": message}, status=status)


@api_view(["POST"])
def delete_project(request):
    try:
        username = request.data.get("username")
        user = User(username=username, password=None)
        user = user.find()

        project_id = request.data.get("project_id")

        store_obj = Store(user)
        err, exception = store_obj.delete(project_id)

        if err:
            raise Exception(exception)

        status, success, message = 200, True, "Project Deleted Successfully"
    except Exception as e:
        status, success, message = 500, False, str(e)
    return JsonResponse({"success": success, "message": message}, status=status)
