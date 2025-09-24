const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");
require("dotenv").config();

const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

// This prints: E:\Projects\httpayer\contracts\functions
console.log("__dirname:", __dirname);

const contractDeployment = require(path.resolve(__dirname, "..", "deployments", "HTTPayerConsumer.json"));
const contractAddress = contractDeployment.deployedTo;

const artifact = require(path.resolve(__dirname, "..", "out", "HTTPayerChainlinkConsumer.sol", "HTTPayerChainlinkConsumer.json"));
const abi = artifact.abi;

const contract = new ethers.Contract(contractAddress, abi, wallet);

const args = [
    "https://demo.httpayer.com/base-weather",
    "GET"
];

const sourceJs = fs.readFileSync(path.join(__dirname, "source.js")).toString();

async function main() {
    const tx = await contract.sendHTTPayerRequest(
        parseInt(process.env.SUBSCRIPTION_ID),
        args,
        300000,
        process.env.DON_ID,
        sourceJs,
    );

    console.log("Tx sent. Waiting for confirmation...");
    await tx.wait();
    console.log("Tx confirmed:", tx.hash);

    // wait a bit before checking s_lastResponse
    await new Promise((resolve) => setTimeout(resolve, 2_000)); // 2s

    const response = await contract.s_lastResponse();
    console.log("Chainlink result:", response);
}

main().catch(console.error);
