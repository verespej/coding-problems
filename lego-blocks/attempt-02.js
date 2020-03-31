'use strict';

const fs = require('fs');

process.stdin.resume();
process.stdin.setEncoding('utf-8');

let inputString = '';
let currentLine = 0;

process.stdin.on('data', inputStdin => {
    inputString += inputStdin;
});

process.stdin.on('end', _ => {
    inputString = inputString.trim().split('\n').map(str => str.trim());

    main();
});

function readLine() {
    return inputString[currentLine++];
}

const cacheForCountAllSingleRowSolutions = {};
function countAllSingleRowSolutions(width, maxBlockSize) {
    const cacheKey = `${maxBlockSize}.${width}`;
    if (cacheKey in cacheForCountAllSingleRowSolutions) {
        return cacheForCountAllSingleRowSolutions[cacheKey];
    }

    const window = [0n, 1n];
    for (let i = 1n; i < maxBlockSize; i++) {
        const next = 2n * window[window.length - 1];
        window.push(next);
    }

    if (width < window.length) {
        cacheForCountAllSingleRowSolutions[cacheKey] = window[width];
        return window[width];
    }

    const sumAll = w => w.reduce((acc, val) => (acc + val), 0n);
    for (let i = window.length - 1; i < width; i++) {
        window.shift();
        const next = sumAll(window);
        window.push(next);
    }

    cacheForCountAllSingleRowSolutions[cacheKey] = window[window.length - 1];
    return window[window.length - 1];
}

function countAllSolutions(height, width, maxBlockSize) {
    const numRowPermutations = countAllSingleRowSolutions(width, maxBlockSize);
    return numRowPermutations ** height;
}

const cacheForCountNonSplitSolutions = {};
function countNonSplitSolutions(height, width, maxBlockSize) {
    const cacheKey = `${maxBlockSize}.${height}.${width}`;
    if (cacheKey in cacheForCountNonSplitSolutions) {
        return cacheForCountNonSplitSolutions[cacheKey];
    }

    let nonSplitSolutions = countAllSolutions(height, width, maxBlockSize);
    for (let i = 1n; i < width; i++) {
        nonSplitSolutions -=
            (countAllSolutions(height, width - i, maxBlockSize)) *
            (countNonSplitSolutions(height, i, maxBlockSize));
    }

    cacheForCountNonSplitSolutions[cacheKey] = nonSplitSolutions;
    return cacheForCountNonSplitSolutions[cacheKey];
}

// n: height
// m: width 
function legoBlocks(n, m) {
    const MAX_BLOCK_SIZE = 4;
    const MAX_RESULT = 10n ** 9n + 7n;
    return countNonSplitSolutions(BigInt(n), BigInt(m), MAX_BLOCK_SIZE) % MAX_RESULT;
}

function main() {
    const ws = fs.createWriteStream(process.env.OUTPUT_PATH);

    const t = parseInt(readLine(), 10);

    for (let tItr = 0; tItr < t; tItr++) {
        const nm = readLine().split(' ');

        const n = parseInt(nm[0], 10);

        const m = parseInt(nm[1], 10);

        let result = legoBlocks(n, m);

        ws.write(result + "\n");
    }

    ws.end();
}
