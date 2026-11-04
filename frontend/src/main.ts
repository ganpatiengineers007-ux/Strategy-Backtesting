import "./styles/base.css";
import "./styles/layout.css";
import "./styles/components.css";
import "./styles/dashboard.css";
import "./styles/extra.css";
import "./styles/global.css";
import { start } from "./app";

start(document.getElementById("app") as HTMLElement, document.getElementById("nav") as HTMLElement);
