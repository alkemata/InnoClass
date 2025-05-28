import axios from "axios";

const api = axios.create({
  baseURL: "https://api.innoclass.alkemata.com",
});

export default api;

