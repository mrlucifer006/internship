package com.ssbs.servlet;

import com.google.gson.Gson;
import com.ssbs.dao.VehicleDAO;
import com.ssbs.model.Vehicle;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class LogisticsServlet extends HttpServlet {
    private final VehicleDAO vehicleDAO = new VehicleDAO();
    private final Gson gson = new Gson();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        PrintWriter out = resp.getWriter();

        String search = req.getParameter("search");
        String status = req.getParameter("status");

        try {
            List<Vehicle> list = vehicleDAO.getVehicles(search, status);
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
            if ("/exit".equals(pathInfo)) {
                Vehicle payload = gson.fromJson(req.getReader(), Vehicle.class);
                if (payload != null && payload.getId() != null) {
                    double tare = payload.getTareWeight() != null ? payload.getTareWeight() : 0.0;
                    boolean ok = vehicleDAO.processExit(payload.getId(), tare);
                    out.print("{\"success\":" + ok + ",\"message\":\"Vehicle clearance complete\"}");
                } else {
                    resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                    out.print("{\"error\":\"Vehicle ID and Tare Weight required\"}");
                }
            } else {
                // Inbound entry
                Vehicle v = gson.fromJson(req.getReader(), Vehicle.class);
                boolean ok = vehicleDAO.addVehicleEntry(v);
                resp.setStatus(HttpServletResponse.SC_CREATED);
                out.print("{\"success\":" + ok + ",\"message\":\"Vehicle entry logged\"}");
            }
        } catch (Exception e) {
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.print("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }
}
