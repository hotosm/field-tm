import http from "k6/http";
import { sleep, check } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
};

export default function () {
  const url = `http://api:8000/${__ENV.url_path}`;
  const res = http.get(url);
  check(res, { "status is 200": (res) => res.status === 200 });
  sleep(1);
}
