// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {FunctionsClient} from "@chainlink/contracts/src/v0.8/functions/dev/v1_0_0/FunctionsClient.sol";
import {ConfirmedOwner} from "@chainlink/contracts/src/v0.8/shared/access/ConfirmedOwner.sol";
import {FunctionsRequest} from "@chainlink/contracts/src/v0.8/functions/dev/v1_0_0/libraries/FunctionsRequest.sol";

contract HTTPayerChainlinkConsumer is FunctionsClient, ConfirmedOwner {
    using FunctionsRequest for FunctionsRequest.Request;

    bytes32 public s_lastRequestId;
    string public s_lastResponse;
    bytes public s_lastError;

    event Response(bytes32 indexed requestId, string response, bytes error);
    event RawResponse(bytes32 requestId, bytes rawResponse);

    constructor(
        address router
    ) FunctionsClient(router) ConfirmedOwner(msg.sender) {}

    function sendHTTPayerRequest(
        uint64 subscriptionId,
        string[] calldata args, // [api_url, method, payload]
        uint32 gasLimit,
        bytes32 donID,
        string memory sourceJs // Inline JavaScript for execution
    ) external onlyOwner returns (bytes32) {
        FunctionsRequest.Request memory req;
        req.initializeRequestForInlineJavaScript(sourceJs);
        if (args.length > 0) {
            req.setArgs(args);
        }

        s_lastRequestId = _sendRequest(
            req.encodeCBOR(),
            subscriptionId,
            gasLimit,
            donID
        );

        return s_lastRequestId;
    }

    function fulfillRequest(
        bytes32 requestId,
        bytes memory response,
        bytes memory err
    ) internal override {
        if (requestId != s_lastRequestId) revert("Mismatched requestId");
        s_lastResponse = string(response);
        s_lastError = err;
        emit Response(requestId, s_lastResponse, err);
        emit RawResponse(requestId, response);
    }
}
