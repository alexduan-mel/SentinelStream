package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.repository.SignalSnapshotRepository;
import com.sentinelstream.service.SignalService;

@Service
public class SignalServiceImpl implements SignalService {
    private final SignalSnapshotRepository signalSnapshotRepository;

    public SignalServiceImpl(SignalSnapshotRepository signalSnapshotRepository) {
        this.signalSnapshotRepository = signalSnapshotRepository;
    }

    @Override
    public List<SignalResponse> listSignals(int limit) {
        return signalSnapshotRepository.fetchLatestSignalsByTicker();
    }
}
