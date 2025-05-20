import axios from "axios";

export const api = axios.create({
  baseURL: "http://api.innoclass.alkemata.com:8000",
});