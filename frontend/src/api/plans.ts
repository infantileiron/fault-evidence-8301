import {request} from './client';export const list=()=>request('/plans');export const create=(body:unknown)=>request('/plans','POST',body);
