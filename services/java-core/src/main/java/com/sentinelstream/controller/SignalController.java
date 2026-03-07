package com.sentinelstream.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.sentinelstream.dto.SignalDetailResponse;
import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.service.SignalService;

import static org.springframework.http.HttpStatus.NOT_FOUND;

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

    @GetMapping("/{id}")
    public ResponseEntity<SignalDetailResponse> getSignalDetail(@PathVariable("id") long id) {
        SignalDetailResponse detail = signalService.getSignalDetail(id);
        if (detail == null) {
            throw new ResponseStatusException(NOT_FOUND, "signal_not_found");
        }
        return ResponseEntity.ok(detail);
    }
}
