import asyncio
import pathlib
import textwrap
from pprint import pprint


ROOT = pathlib.Path(__file__).parent


async def read_all(r: asyncio.StreamReader):
    output = ''

    while recv := await r.read(1024):
        output += recv.decode("utf8")

        if len(recv) < 1024:
            break

    return output


def parse_req(req: str):
    line_iter = iter(req.rstrip().splitlines())

    # 1st line is head, all other can just be put into dict
    method, dir_, http_ver = next(line_iter).split()

    req_dict = {
        'Method': method,
        'Directory': "" if dir_ == "/" else dir_,
        'HTTP': http_ver
    }

    for line in line_iter:
        key, val = line.split(": ")
        req_dict[key] = val

    return req_dict


def file_list_html_gen(path: pathlib.Path):

    for sub_path in path.iterdir():

        if path == ROOT:
            relative = '/'
        else:
            relative = '/' + str(path.relative_to(ROOT)).strip('./') + '/'

        file_name = sub_path.name

        if sub_path.is_dir():
            yield f'<a href="{relative}{file_name}">{file_name}</a>'
        else:
            yield f'<a href="{relative}{file_name}" download="{file_name}">{file_name}</a>'


def create_resp(req_dict: dict):

    # reject user when POST or other stuffs are used
    if req_dict['Method'] != 'GET':
        return f"{req_dict['HTTP']} 405 Method Not Allowed\r\nConnection: close\r\n\r\n", None

    # reject user when accessing not existing directory
    dir_ = ROOT.joinpath(req_dict["Directory"][1:])

    if not dir_.exists():
        return f"{req_dict['HTTP']} 404 Not Found\r\nConnection: close\r\n\r\n", None

    # else build html for directory
    if dir_.is_dir():
        try:
            parent_str = str(dir_.parent.relative_to(ROOT)).strip('./')

        except ValueError:
            parent_str = ""

        parent_dir = f'<a href="/{parent_str}">Go Up</a><br>'
        path_list = parent_dir + '<br>'.join(file_list_html_gen(dir_))

        resp = f"{req_dict['HTTP']} 200 OK\r\n" \
               f"Content-Type: text/html\r\n" \
               f"Content-Length: {len(path_list.encode('utf8'))}\r\n" \
               f"Connection: close\r\n\r\n" \
               f"{path_list}"

        attach = None

    else:
        # else send file
        attach = dir_.read_bytes()

        resp = f"{req_dict['HTTP']} 200 OK\r\n" \
               f"Content-Type: application/octet-stream\r\n" \
               f"Content-Length: {len(attach)}\r\n" \
               f"Connection: close\r\n\r\n"

    return resp, attach


async def tcp_handler(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    # Receive
    print("\nReceiving")

    parsed = parse_req(await read_all(r))
    pprint(parsed)

    print("Received")

    resp, file = create_resp(parsed)

    # Respond
    print("\nResponding", textwrap.indent(resp, " "), sep='\n')
    w.write(resp.encode('utf8'))
    if file:
        print("File length:", len(file))
        w.write(file)
    await w.drain()
    w.close()

    print("Response sent")


async def serve_files():
    server = await asyncio.start_server(tcp_handler, '127.0.0.1', 80)

    print("Started")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(serve_files())