import "@mysubscription/user_menu";
import { registry } from "@web/core/registry";

// Deployment policy: keep native user-menu behavior except this single entry.
registry.category("user_menuitems").remove("mysubscription_user_menu");
