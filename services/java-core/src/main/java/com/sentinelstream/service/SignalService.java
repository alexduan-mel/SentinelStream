package com.sentinelstream.service;

import java.util.List;

import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.dto.SignalDetailResponse;

public interface SignalService {
    List<SignalResponse> listSignals(int limit);

    SignalDetailResponse getSignalDetail(long id);
}
