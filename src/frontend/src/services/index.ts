import axios from 'axios';

const VITE_API_URL = import.meta.env.VITE_API_URL;

export const api = axios.create({
  baseURL: VITE_API_URL,
  withCredentials: true,
});
