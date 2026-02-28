package com.sentinelstream.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.service.SignalService;

@RestController
@RequestMapping("/api/signals")
public class SignalController {
    private final SignalService signalService;

    public SignalController(SignalService signalService) {
        this.signalService = signalService;
    }

    @GetMapping
    public ResponseEntity<List<SignalResponse>> listSignals(
        @RequestParam(name = "limit", defaultValue = "20") int limit
    ) {
        return ResponseEntity.ok(signalService.listSignals(limit));
    }
}
