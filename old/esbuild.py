ESBUILD_BINARY_LOCATION=r"C:\Users\danny\OneDrive\Documents\code\rotaplanner\frontend\.yarn\unplugged\@esbuild-win32-x64-npm-0.17.18-97886df625\node_modules\@esbuild\win32-x64\esbuild.exe"

from functools import wraps
from itertools import islice
import subprocess
from typing import Generator, Iterable

#subprocess.run(ESBUILD_BINARY_LOCATION)

""" // The JavaScript API communicates with the Go child process over stdin/stdout
// using this protocol. It's a very simple binary protocol that uses primitives
// and nested arrays and maps. It's basically JSON with UTF-8 encoding and an
// additional byte array primitive. You must send a response after receiving a
// request because the other end is blocking on the response coming back.

import type * as types from "./types"

export interface BuildRequest {
  command: 'build'
  key: number
  entries: [string, string][]; // Use an array instead of a map to preserve order
  flags: string[]
  write: boolean
  stdinContents: Uint8Array | null
  stdinResolveDir: string | null
  absWorkingDir: string
  nodePaths: string[]
  context: boolean
  plugins?: BuildPlugin[]
  mangleCache?: Record<string, string | false>
}

export interface ServeRequest {
  command: 'serve'
  key: number
  onRequest: boolean
  port?: number
  host?: string
  servedir?: string
  keyfile?: string
  certfile?: string
}

export interface ServeResponse {
  port: number
  host: string
}

export interface BuildPlugin {
  name: string
  onStart: boolean
  onEnd: boolean
  onResolve: { id: number, filter: string, namespace: string }[]
  onLoad: { id: number, filter: string, namespace: string }[]
}

export interface BuildResponse {
  errors: types.Message[]
  warnings: types.Message[]
  outputFiles?: BuildOutputFile[]
  metafile?: string
  mangleCache?: Record<string, string | false>
  writeToStdout?: Uint8Array
}

export interface OnEndRequest extends BuildResponse {
  command: 'on-end'
}

export interface OnEndResponse {
  errors: types.Message[]
  warnings: types.Message[]
}

export interface BuildOutputFile {
  path: string
  contents: Uint8Array
}

export interface PingRequest {
  command: 'ping'
}

export interface RebuildRequest {
  command: 'rebuild'
  key: number
}

export interface RebuildResponse {
  errors: types.Message[]
  warnings: types.Message[]
}

export interface DisposeRequest {
  command: 'dispose'
  key: number
}

export interface CancelRequest {
  command: 'cancel'
  key: number
}

export interface WatchRequest {
  command: 'watch'
  key: number
}

export interface OnServeRequest {
  command: 'serve-request'
  key: number
  args: types.ServeOnRequestArgs
}

export interface TransformRequest {
  command: 'transform'
  flags: string[]
  input: Uint8Array
  inputFS: boolean
  mangleCache?: Record<string, string | false>
}

export interface TransformResponse {
  errors: types.Message[]
  warnings: types.Message[]

  code: string
  codeFS: boolean

  map: string
  mapFS: boolean

  legalComments?: string
  mangleCache?: Record<string, string | false>
}

export interface FormatMsgsRequest {
  command: 'format-msgs'
  messages: types.Message[]
  isWarning: boolean
  color?: boolean
  terminalWidth?: number
}

export interface FormatMsgsResponse {
  messages: string[]
}

export interface AnalyzeMetafileRequest {
  command: 'analyze-metafile'
  metafile: string
  color?: boolean
  verbose?: boolean
}

export interface AnalyzeMetafileResponse {
  result: string
}

export interface OnStartRequest {
  command: 'on-start'
  key: number
}

export interface OnStartResponse {
  errors?: types.PartialMessage[]
  warnings?: types.PartialMessage[]
}

export interface ResolveRequest {
  command: 'resolve'
  key: number
  path: string
  pluginName: string
  importer?: string
  namespace?: string
  resolveDir?: string
  kind?: string
  pluginData?: number
}

export interface ResolveResponse {
  errors: types.Message[]
  warnings: types.Message[]

  path: string
  external: boolean
  sideEffects: boolean
  namespace: string
  suffix: string
  pluginData: number
}

export interface OnResolveRequest {
  command: 'on-resolve'
  key: number
  ids: number[]
  path: string
  importer: string
  namespace: string
  resolveDir: string
  kind: types.ImportKind
  pluginData: number
}

export interface OnResolveResponse {
  id?: number
  pluginName?: string

  errors?: types.PartialMessage[]
  warnings?: types.PartialMessage[]

  path?: string
  external?: boolean
  sideEffects?: boolean
  namespace?: string
  suffix?: string
  pluginData?: number

  watchFiles?: string[]
  watchDirs?: string[]
}

export interface OnLoadRequest {
  command: 'on-load'
  key: number
  ids: number[]
  path: string
  namespace: string
  suffix: string
  pluginData: number
}

export interface OnLoadResponse {
  id?: number
  pluginName?: string

  errors?: types.PartialMessage[]
  warnings?: types.PartialMessage[]

  contents?: Uint8Array
  resolveDir?: string
  loader?: string
  pluginData?: number

  watchFiles?: string[]
  watchDirs?: string[]
}

////////////////////////////////////////////////////////////////////////////////

export interface Packet {
  id: number
  isRequest: boolean
  value: Value
}

export type Value =
  | null
  | boolean
  | number
  | string
  | Uint8Array
  | Value[]
  | { [key: string]: Value }
 """

def logfunc(func):
  @wraps(func)
  def innerfunc(*args,**kwargs):
    retval=func(*args,**kwargs)
    print(func,args,kwargs,retval)
    return retval
  return innerfunc
    
def encode_seq(seq):
  byteseq=bytes(seq)
  yield from len(byteseq).to_bytes(4,byteorder='little')
  yield from byteseq
  print('enc seq',len(byteseq).to_bytes(4,byteorder='little'),byteseq)
  

def encodePacket(packet):
  def visit(value)->Generator[int,None,None]:
    if value is None:
      yield 0
    elif isinstance(value,bool):
      yield 1
      yield int(value)
    elif isinstance(value,int):
      yield 2
      yield from value.to_bytes(4,byteorder='little')
    elif isinstance(value,str):
      yield 3
      yield from encode_seq(value.encode())
    elif isinstance(value,bytes):
      yield 4
      yield from encode_seq(value)
    elif isinstance(value,list):
      yield 5
      yield from len(value).to_bytes(4,byteorder='little')
      for item in value:
        yield from visit(item)
    else:
      assert isinstance(value,dict)
      yield 6
      yield from len(value).to_bytes(4,byteorder='little')
      for key in value:
        yield from encode_seq(key.encode())
        yield from visit(value[key])
      
  packetid=((packet['id']<<1)+(0 if packet['isRequest'] else 1))
  payload=packetid.to_bytes(4,byteorder='little')+bytes(visit(packet['value']))
  return payload
  return len(payload).to_bytes(4,byteorder='little')+payload
  
 
def read32(bytestream):
  return int.from_bytes(bytes(islice(bytestream,4)),byteorder='little')

 
def read_seq(bytestream):
  l=read32(bytestream)
  return bytes(islice(bytestream,l))

def decodePacket(bytestream):
  bb=iter(bytestream)
   
  def visit():
    chunktype=next(bb)
    print('chunktype',chunktype)
    match chunktype:
      case 0: #// null
        return None
      case 1: #// boolean
        return bool(next(bb))
      case 2: #// number
        return read32(bb)
      case 3: #// string
        return bytes.decode(read_seq(bb))
      case 4: #// Uint8Array
        return read_seq(bb)
      case 5: #{ // Value[]
        count = read32(bb)
        value = []
        while len(value)<count:
          value.append(visit())
        return value
      case 6: #{ // { [key: string]: Value }
        count = read32(bb)
        value = {}
        while len(value)<count:
          key=read_seq(bb).decode()
          value[key] = visit()
          print(key,value)
        return value
      case _:
        raise ValueError('Invalid packet')
    
  

  
  packetid = read32(bb)
  
  isRequest = (packetid & 1) == 0
  packetid >>= 1
  print(packetid)
  value = visit()
  try:
    next(bb)
    raise ValueError('invalid packet')
  except StopIteration:
    pass
  return {'id':packetid, 'isRequest':isRequest, 'value':value }

test_packet={'id':1,'isRequest':False,'value':{'complex':'payload','j':[1,2,3]}}
enc=encodePacket(test_packet)
print(decodePacket(enc))