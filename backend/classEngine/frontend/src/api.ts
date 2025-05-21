import axios from "axios";

export const api = axios.create({
  baseURL: "https://api.innoclass.alkemata.com:8000",
});