package com.ssbs.servlet;

import com.google.gson.Gson;
import com.ssbs.dao.VisitorDAO;
import com.ssbs.model.Visitor;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class VisitorServlet extends HttpServlet {
    private final VisitorDAO visitorDAO = new VisitorDAO();
    private final Gson gson = new Gson();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        PrintWriter out = resp.getWriter();

        String search = req.getParameter("search");
        String statusStr = req.getParameter("status");
        Integer status = (statusStr != null && !statusStr.isEmpty()) ? Integer.parseInt(statusStr) : null;

        try {
            List<Visitor> list = visitorDAO.getVisitors(search, status);
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
            if ("/checkout".equals(pathInfo)) {
                String idStr = req.getParameter("id");
                if (idStr == null || idStr.isEmpty()) {
                    Visitor payload = gson.fromJson(req.getReader(), Visitor.class);
                    if (payload != null && payload.getId() != null) idStr = String.valueOf(payload.getId());
                }
                if (idStr != null) {
                    boolean ok = visitorDAO.checkOutVisitor(Long.parseLong(idStr));
                    out.print("{\"success\":" + ok + ",\"message\":\"Checked out\"}");
                } else {
                    resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                    out.print("{\"error\":\"Visitor ID required\"}");
                }
            } else {
                // Register visitor
                Visitor v = gson.fromJson(req.getReader(), Visitor.class);
                if (v == null) {
                    v = new Visitor();
                    v.setName(req.getParameter("name"));
                    v.setPhone(req.getParameter("phone"));
                    v.setPersonToVisit(req.getParameter("person_to_visit"));
                    v.setReason(req.getParameter("reason"));
                    v.setIdType(req.getParameter("id_type"));
                    v.setIdNumber(req.getParameter("id_number"));
                    v.setVehicleNumber(req.getParameter("vehicle_number"));
                    v.setHasVehicle(req.getParameter("has_vehicle") != null);
                }
                v.setBadgeNumber("V-2026-" + (1000 + new Random().nextInt(9000)));

                boolean ok = visitorDAO.addVisitor(v);
                resp.setStatus(HttpServletResponse.SC_CREATED);
                Map<String, Object> res = new HashMap<>();
                res.put("success", ok);
                res.put("data", v);
                out.print(gson.toJson(res));
            }
        } catch (Exception e) {
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.print("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }
}
