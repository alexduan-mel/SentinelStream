package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.MonitorRowResponse;
import com.sentinelstream.repository.MonitorRepository;
import com.sentinelstream.service.MonitorService;

@Service
public class MonitorServiceImpl implements MonitorService {
    private final MonitorRepository monitorRepository;

    public MonitorServiceImpl(MonitorRepository monitorRepository) {
        this.monitorRepository = monitorRepository;
    }

    @Override
    public List<MonitorRowResponse> getMonitorSnapshot(int limitPerTicker) {
        return monitorRepository.fetchMonitorSnapshot();
    }
}
