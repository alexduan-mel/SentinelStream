package com.sentinelstream.service;

import java.util.List;

import com.sentinelstream.dto.SignalResponse;

public interface SignalService {
    List<SignalResponse> listSignals(int limit);
}
