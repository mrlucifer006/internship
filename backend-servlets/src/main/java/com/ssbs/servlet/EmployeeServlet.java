package com.ssbs.servlet;

import com.google.gson.Gson;
import com.ssbs.dao.EmployeeDAO;
import com.ssbs.model.Employee;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class EmployeeServlet extends HttpServlet {
    private final EmployeeDAO employeeDAO = new EmployeeDAO();
    private final Gson gson = new Gson();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        PrintWriter out = resp.getWriter();

        String search = req.getParameter("search");
        String roleStr = req.getParameter("role");
        String statusStr = req.getParameter("status");

        Integer role = (roleStr != null && !roleStr.isEmpty()) ? Integer.parseInt(roleStr) : null;
        Integer status = (statusStr != null && !statusStr.isEmpty()) ? Integer.parseInt(statusStr) : null;

        try {
            List<Employee> list = employeeDAO.getEmployees(search, role, status);
            Map<String, Object> res = new HashMap<>();
            res.put("success", true);
            res.put("count", list.size());
            res.put("data", list);
            out.print(gson.toJson(res));
        } catch (Exception e) {
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.print("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        PrintWriter out = resp.getWriter();
        String pathInfo = req.getPathInfo();

        try {
            if ("/status".equals(pathInfo)) {
                String loginId = req.getParameter("login_id");
                int newStatus = Integer.parseInt(req.getParameter("status"));
                employeeDAO.updateStatus(loginId, newStatus);
                out.print("{\"success\":true,\"message\":\"Status updated\"}");
            } else if ("/delete".equals(pathInfo)) {
                String loginId = req.getParameter("login_id");
                boolean ok = employeeDAO.deleteEmployee(loginId);
                out.print("{\"success\":" + ok + ",\"message\":\"Employee deleted\"}");
            } else {
                Employee emp = gson.fromJson(req.getReader(), Employee.class);
                boolean ok = employeeDAO.createEmployee(emp);
                resp.setStatus(HttpServletResponse.SC_CREATED);
                out.print("{\"success\":" + ok + ",\"message\":\"Employee provisioned\"}");
            }
        } catch (Exception e) {
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.print("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }
}
