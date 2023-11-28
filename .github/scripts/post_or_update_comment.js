#!/usr/bin/env node
// Copyright 2023 Efabless Corporation
//
// Licensed under the Apache License, Version 2.0(the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * 
 * @param {Octokit} github 
 * @param {object} context 
 * @param {string} botUsername 
 * @param {string} body 
 */
module.exports = async function (github, context, botUsername, body) {
    const METRIC_REPORT_MARK = "<!-- MARK: METRICS REPORT -->";

    let page = 1;
    let allComments = [];
    let comments = [];
    do {
        let response = await github.request("GET /repos/{owner}/{repo}/issues/{issue_number}/comments?page={page}&per_page=100", {
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            page,
        });
        comments = response.data;
        allComments = allComments.concat(comments);
        page += 1;
    } while (comments.length != 0);

    let found = null;
    for (let comment of allComments) {
        if (comment.body.includes(METRIC_REPORT_MARK) && comment.user.login == botUsername) {
            found = comment;
            break;
        }
    }

    let fn = github.rest.issues.createComment;
    let request = {
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `${METRIC_REPORT_MARK}\n\n${body}`
    };

    if (found) {
        request.comment_id = found.id;
        fn = github.rest.issues.updateComment;
    }

    await fn(request);
}