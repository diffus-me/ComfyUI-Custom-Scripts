from server import PromptServer
from aiohttp import web
import os
import inspect
import json
import importlib
import sys

import execution_context
import folder_paths

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pysssss

# root_directory = os.path.dirname(inspect.getfile(PromptServer))
# workflows_directory = os.path.join(root_directory, "pysssss-workflows")
# workflows_directory = pysssss.get_config_value(
#     "workflows.directory", workflows_directory)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def get_workflows_directory(request):
    context = execution_context.ExecutionContext(request)
    return os.path.join(folder_paths.get_user_directory(context.user_hash), 'workflows')


@PromptServer.instance.routes.get("/pysssss/workflows")
async def get_workflows(request):
    files = []
    for dirpath, directories, file in os.walk(get_workflows_directory(request)):
        for file in file:
            if (file.endswith(".json")):
                files.append(os.path.relpath(os.path.join(
                    dirpath, file), get_workflows_directory(request)))
    return web.json_response(list(map(lambda f: os.path.splitext(f)[0].replace("\\", "/"), files)))


@PromptServer.instance.routes.get("/pysssss/workflows/{name:.+}")
async def get_workflow(request):
    file = os.path.abspath(os.path.join(
        get_workflows_directory(request), request.match_info["name"] + ".json"))
    if os.path.commonpath([file, get_workflows_directory(request)]) != get_workflows_directory(request):
        return web.Response(status=403)

    return web.FileResponse(file)


@PromptServer.instance.routes.post("/pysssss/workflows")
async def save_workflow(request):
    json_data = await request.json()
    file = os.path.abspath(os.path.join(
        get_workflows_directory(request), json_data["name"] + ".json"))
    if os.path.commonpath([file, get_workflows_directory(request)]) != get_workflows_directory(request):
        return web.Response(status=403)

    if os.path.exists(file) and ("overwrite" not in json_data or json_data["overwrite"] == False):
        return web.Response(status=409)

    sub_path = os.path.dirname(file)
    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    with open(file, "w") as f:
        f.write(json.dumps(json_data["workflow"]))

    return web.Response(status=201)
