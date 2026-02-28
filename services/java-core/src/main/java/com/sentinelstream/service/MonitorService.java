package com.sentinelstream.service;

import java.util.List;

import com.sentinelstream.dto.MonitorRowResponse;

public interface MonitorService {
    List<MonitorRowResponse> getMonitorSnapshot(int limitPerTicker);
}
