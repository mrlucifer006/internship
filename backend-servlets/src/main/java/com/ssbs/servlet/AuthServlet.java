package com.ssbs.servlet;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.ssbs.dao.EmployeeDAO;
import com.ssbs.model.Employee;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;

public class AuthServlet extends HttpServlet {
    private final EmployeeDAO employeeDAO = new EmployeeDAO();
    private final Gson gson = new Gson();

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        PrintWriter out = resp.getWriter();
        String pathInfo = req.getPathInfo();

        if (pathInfo == null || "/login".equals(pathInfo)) {
            BufferedReader reader = req.getReader();
            JsonObject json = gson.fromJson(reader, JsonObject.class);

            String username = json != null && json.has("username") ? json.get("username").getAsString() : req.getParameter("username");
            String password = json != null && json.has("password") ? json.get("password").getAsString() : req.getParameter("password");

            try {
                Employee emp = employeeDAO.authenticate(username, password);
                if (emp != null) {
                    HttpSession session = req.getSession(true);
                    session.setAttribute("user", emp);

                    Map<String, Object> res = new HashMap<>();
                    res.put("success", true);
                    res.put("user", emp);
                    out.print(gson.toJson(res));
                } else {
                    resp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                    Map<String, Object> res = new HashMap<>();
                    res.put("success", false);
                    res.put("message", "Invalid login credentials");
                    out.print(gson.toJson(res));
                }
            } catch (Exception e) {
                resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                out.print("{\"error\":\"" + e.getMessage() + "\"}");
            }
        } else if ("/logout".equals(pathInfo)) {
            HttpSession session = req.getSession(false);
            if (session != null) {
                Employee emp = (Employee) session.getAttribute("user");
                if (emp != null) {
                    try {
                        employeeDAO.updateStatus(emp.getLoginId(), 0);
                    } catch (Exception ignored) {}
                }
                session.invalidate();
            }
            out.print("{\"success\":true,\"message\":\"Logged out\"}");
        }
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        HttpSession session = req.getSession(false);
        if (session != null && session.getAttribute("user") != null) {
            resp.getWriter().print(gson.toJson(session.getAttribute("user")));
        } else {
            resp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            resp.getWriter().print("{\"authenticated\":false}");
        }
    }
}
