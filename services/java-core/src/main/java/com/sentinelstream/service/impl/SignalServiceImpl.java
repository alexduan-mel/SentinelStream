package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.EvidenceItemResponse;
import com.sentinelstream.dto.SignalDetailResponse;
import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.repository.SignalDetailRepository;
import com.sentinelstream.repository.SignalSnapshotRepository;
import com.sentinelstream.service.SignalService;

@Service
public class SignalServiceImpl implements SignalService {
    private final SignalDetailRepository signalDetailRepository;
    private final SignalSnapshotRepository signalSnapshotRepository;

    public SignalServiceImpl(
        SignalDetailRepository signalDetailRepository,
        SignalSnapshotRepository signalSnapshotRepository
    ) {
        this.signalDetailRepository = signalDetailRepository;
        this.signalSnapshotRepository = signalSnapshotRepository;
    }

    @Override
    public List<SignalResponse> listSignals(int limit) {
        return signalSnapshotRepository.fetchLatestSignalsByTicker();
    }

    @Override
    public SignalDetailResponse getSignalDetail(long id) {
        SignalDetailResponse base = signalDetailRepository.fetchSignalDetail(id);
        if (base == null) {
            return null;
        }
        List<EvidenceItemResponse> evidence = signalDetailRepository.fetchEvidenceItems(base.ticker());
        return new SignalDetailResponse(
            base.analysisId(),
            base.ticker(),
            base.sentiment(),
            base.confidence(),
            base.summary(),
            base.publishedAt(),
            base.title(),
            base.url(),
            base.publisher(),
            evidence
        );
    }
}
