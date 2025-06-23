module("luci.controller.status_all", package.seeall)

function index()
  entry({"admin", "status", "include", "status_all"}, call("action_status_all")).leaf = true
end

function action_status_all()
  luci.template.render("status/include/status_all")
end
