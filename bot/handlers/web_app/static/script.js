let state = {
    year1: null,
    direction1: null,
    profile1: null,
    year2: null,
    direction2: null,
    profile2: null
};
let currentSemester = 1;
let maxSemesters = 0;
let firstPlan = null;
let secondPlan = null;

function setMainButtonVisible(visible) {
    var mainButton = Telegram.WebApp.MainButton;
    if (!visible) {
        mainButton.hide();
    } else {
        mainButton.show();
    }
}

function filterPlans(year, direction, profile) {
    return plans.filter(plan => {
        if (year && plan.year !== year) {
            return false;
        }
        if (direction && plan.education_direction !== direction) {
            return false;
        }
        if (profile && plan.profile !== profile) {
            return false;
        }
        return true;
    });
}

function updateSelect(selectId, items, valueField) {
    const select = $(`#${selectId}`);
    select.empty();

    items.forEach(item => {
        const option = $('<option>', {
            value: item[valueField],
            text: item[valueField]
        });
        select.append(option);
    });

    select.prop('disabled', items.length === 0);
}

function getOnlyUnique(arrayOfObjects, field) {
    const unique = [];
    const uniqueValues = [];
    arrayOfObjects.forEach(item => {
        if (!uniqueValues.includes(item[field])) {
            unique.push(item);
            uniqueValues.push(item[field]);
        }
    });

    unique.sort((a, b) => {
        if (a[field] < b[field]) {
            return -1;
        }
        if (a[field] > b[field]) {
            return 1;
        }
        return 0;
    });

    return unique;
}


function updateState(field, value) {
    state[field] = value;

    if (field.startsWith("year")) {
        const directions = filterPlans(Number(state[field]));
        updateSelect(`direction-select-${field.slice(-1)}`, getOnlyUnique(directions, 'education_direction'), 'education_direction');
    } else if (field.startsWith("direction")) {
        const profiles = filterPlans(Number(state[`year${field.slice(-1)}`]), state[field]);
        updateSelect(`profile-select-${field.slice(-1)}`, getOnlyUnique(profiles, 'profile'), 'profile');
        state[`profile${field.slice(-1)}`] = profiles.length > 0 ? profiles[0].profile : null;
    }

    if ((state.year1 && state.direction1 && state.profile1 && state.year2 && state.direction2 && state.profile2)) {
        setMainButtonVisible(true);
    } else {
        setMainButtonVisible(false);
    }
}

const defaultYear1 = $('#year-select-1').val();
const defaultYear2 = $('#year-select-2').val();

updateState('year1', defaultYear1);
updateState('year2', defaultYear2);

const defaultDirection1 = $('#direction-select-1').val();
const defaultDirection2 = $('#direction-select-2').val();

updateState('direction1', defaultDirection1);
updateState('direction2', defaultDirection2);

const defaultProfile1 = $('#profile-select-1').val();
const defaultProfile2 = $('#profile-select-2').val();

updateState('profile1', defaultProfile1);
updateState('profile2', defaultProfile2);

$('select').on('change', function () {
    updateState(this.id.replace('-select-', ''), $(this).val());
});

$('body').css('visibility', '');



Telegram.WebApp.ready();
Telegram.WebApp.expand();

var initData = Telegram.WebApp.initData || '';
var initDataUnsafe = Telegram.WebApp.initDataUnsafe || {};

function checkSemesterButtons(maxSemesters) {
    $("#prev-semester").prop('disabled', currentSemester === 1);
    $("#next-semester").prop('disabled', currentSemester === maxSemesters);
}

$("#prev-semester").click(function () {
    currentSemester--;
    updateSemesterTable(currentSemester);
    checkSemesterButtons(maxSemesters);
});

$("#next-semester").click(function () {
    currentSemester++;
    updateSemesterTable(currentSemester);
    checkSemesterButtons(maxSemesters);
});

function updateSemesterTable(semester) {
    const tableBody = $("#compare-table tbody");
    tableBody.empty();

    const firstPlanDisciplines = firstPlan.disciplines.filter(
        discipline => discipline.semester === semester
    );
    const secondPlanDisciplines = secondPlan.disciplines.filter(
        discipline => discipline.semester === semester
    );

    firstPlanDisciplines.forEach(discipline => {
        const tableRow = $("<tr>");

        const disciplineNameCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: discipline.name.text
        });
        tableRow.append(disciplineNameCell);

        const firstPlanCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: "✓"
        });
        tableRow.append(firstPlanCell);

        const secondPlanDiscipline = secondPlanDisciplines.find(
            d => d.name.text === discipline.name.text
        );
        const secondPlanCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: secondPlanDiscipline ? "✓" : "✗",
            css: {
                "color": secondPlanDiscipline ? "" : "#ea5748"
            }
        });
        tableRow.append(secondPlanCell);

        tableBody.append(tableRow);
    });

    secondPlanDisciplines.forEach(discipline => {
        if (!firstPlanDisciplines.find(d => d.name.text === discipline.name.text)) {
            const tableRow = $("<tr>");

            const disciplineNameCell = $("<td>", {
                class: "px-3 py-4 text-sm",
                text: discipline.name.text
            });
            tableRow.append(disciplineNameCell);

            const firstPlanCell = $("<td>", {
                class: "px-3 py-4 text-sm",
                text: "✗",
                css: {
                    "color": "#ea5748"
                }
            });
            tableRow.append(firstPlanCell);

            const secondPlanCell = $("<td>", {
                class: "px-3 py-4 text-sm",
                text: "✓"
            });
            tableRow.append(secondPlanCell);

            tableBody.append(tableRow);
        }
    });

    $("#semester-label").text(`Семестр ${semester}`);

    $("#compare-table").removeClass("hidden");
}






let comparisonBySemesters = true;

$("#toggle-comparison-mode").click(function () {
    comparisonBySemesters = !comparisonBySemesters;

    if (comparisonBySemesters) {
        $("#toggle-comparison-mode").text("Переключить на сравнение всех предметов");
        updateSemesterTable(currentSemester);
        $("#semester-controls").show();
    } else {
        $("#toggle-comparison-mode").text("Переключить на сравнение по семестрам");
        updateAllSubjectsTable();
        $("#semester-controls").hide();
    }
});

function updateAllSubjectsTable() {
    const tableBody = $("#compare-table tbody");
    tableBody.empty();

    const allFirstPlanDisciplines = firstPlan.disciplines;
    const allSecondPlanDisciplines = secondPlan.disciplines;

    const allDisciplines = [...allFirstPlanDisciplines, ...allSecondPlanDisciplines];
    console.log(allDisciplines);
    const uniqueDisciplines = allDisciplines.reduce((acc, discipline) => {
        if (!acc.find(d => d.name.text === discipline.name.text)) {
            acc.push(discipline);
        }

        return acc;
    }, []);

    console.log(uniqueDisciplines);

    uniqueDisciplines.forEach(discipline => {
        const tableRow = $("<tr>");

        const disciplineNameCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: discipline.name.text
        });
        tableRow.append(disciplineNameCell);

        const firstPlanDiscipline = allFirstPlanDisciplines.find(
            d => d.name.text === discipline.name.text
        );
        const firstPlanCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: firstPlanDiscipline ? "✓" : "✗",
            css: {
                "color": firstPlanDiscipline ? "" : "#ea5748"
            }
        });
        tableRow.append(firstPlanCell);

        const secondPlanDiscipline = allSecondPlanDisciplines.find(
            d => d.name.text === discipline.name.text
        );
        const secondPlanCell = $("<td>", {
            class: "px-3 py-4 text-sm",
            text: secondPlanDiscipline ? "✓" : "✗",
            css: {
                "color": secondPlanDiscipline ? "" : "#ea5748"
            }
        });
        tableRow.append(secondPlanCell);

        tableBody.append(tableRow);
    });

    $("#semester-label").text("Все предметы");
}


Telegram.WebApp.MainButton
    .setText('Сравнить')
    .onClick(function () {
        const data = {
            _auth: initData,
            year1: state.year1,
            direction1: state.direction1,
            profile1: state.profile1,
            year2: state.year2,
            direction2: state.direction2,
            profile2: state.profile2
        }

        $.ajax('/getCompareResult', {
            type: 'POST',
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: 'json',
            success: function (result) {
                Telegram.WebApp.BackButton.show().onClick(function () {
                    $("#select-plans-section").removeClass("hidden");
                    $("#compare-section").addClass("hidden");
                    Telegram.WebApp.BackButton.hide();
                });

                firstPlan = result.first_plan;
                secondPlan = result.second_plan;

                $("#select-plans-section").addClass("hidden");
                $("#compare-section").removeClass("hidden");
                setMainButtonVisible(false);

                const tableBody = $("#compare-table tbody");
                tableBody.empty();

                if (firstPlan === null) {
                    alert(`Не удалось получить план ${state.year1} года по направлению ${state.direction1} профилю ${state.profile1}`);
                    return;
                }

                if (secondPlan === null) {
                    alert(`Не удалось получить план ${state.year2} года по направлению ${state.direction2} профилю ${state.profile2}`);
                    return;
                }

                const maxFirst = Math.max(...firstPlan.disciplines.map(discipline => discipline.semester));
                const maxSecond = Math.max(...secondPlan.disciplines.map(discipline => discipline.semester));

                maxSemesters = Math.min(
                    maxFirst,
                    maxSecond
                );

                console.log(firstPlan);

                if (maxFirst != maxSecond) {
                    alert(`Количество семестров в планах не совпадает! Мы ограничили сравнение до ${maxSemesters} семестров`);
                }

                currentSemester = 1;
                updateSemesterTable(currentSemester);
                checkSemesterButtons(maxSemesters);

                $("#compare-table").removeClass("hidden");

                $("#compare-section").prepend(
                    $("<div>", {
                        id: 'first-plan-name',
                        class: "text-left text-sm",
                        text: `Учебный план 1: ${firstPlan.profile} (${firstPlan.year})`
                    })
                );

                $("#compare-section").prepend(
                    $("<div>", {
                        id: 'second-plan-name',
                        class: "text-left text-sm",
                        text: `Учебный план 2: ${secondPlan.profile} (${secondPlan.year})`
                    })
                );
            },
            error: function (xhr) {
                alert('Ошибка сервера');
            }
        });
    });


